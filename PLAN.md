# Tollgate Infrastructure Kit — Implementation Plan

## Overview

A single Ansible-based repository that deploys all Tollgate-related infrastructure services on a single VPS with one command. Designed for anyone to run Tollgate infrastructure without depending on a small set of operators.

## Target Environment

- **OS**: Debian 13 (trixie) x86_64
- **Access**: SSH key-based (`debian@<VPS_IP>`)
- **Domain**: User brings their own (`BASE_DOMAIN` variable)
- **Secrets**: `.env` file (not committed to git)

## Services (18 total)

| # | Service | Subdomain | Internal Port | Install Method |
|---|---------|-----------|---------------|----------------|
| 1 | Caddy (reverse proxy) | gateway | 80/443 | Docker + xcaddy (with cloudflare plugin) |
| 2 | strfry (general Nostr relay) | `relay.` | 7777 | Docker |
| 3 | obelisk-relay (NIP-29 group chat) | `chat.` | 8080 | Docker (GHCR prebuilt) |
| 4 | blossom-server (blob storage) | `blossom.` | 3001 | Docker (build from hzrd149/blossom-server) |
| 5 | nsite-gateway (Nostr site gateway) | `nsite.` | 3002 | Docker (build from hzrd149/nsite-gateway) |
| 6 | tollgate-release-explorer | `releases.` | — | Static build, Caddy file_server |
| 7 | hive-ci-site | `ci.` | — | Static build, Caddy file_server |
| 8 | Cashu mint infrastructure | `*.mints.` | 8085-8088, 50051-50054 | 4 CDK mintd containers (sat unit, mapped to MB/KB/GB/min in UI) |
| 9 | cashu-brrr (money printer) | `print.mints.` | — | Static build, Caddy file_server |
| 10 | Mint operator proxy | `print.mints./api/` | 3000 | Node.js systemd (tsx) |
| 11 | MPTCP server | none | 65101/65001 | Systemd |
| 12 | FIPS (mesh network) | none | TUN | Systemd (Debian package) |
| 13 | nsyte CLI | N/A | N/A | Deno binary in PATH |
| 14 | GRASP server (ngit-grasp) | `git.` | 7334 | Systemd (built from source) |
| 15 | Routstr AI inference node | `routstr.` | 8000 | Docker (ghcr.io/routstr/proxy) |
| 16 | Routstr Tor hidden service | `.onion` | 80 | Docker (tor-hidden-service) |
| 17 | Auditable Voting (static) | `vote.` | — | Static build (React+Vite+WASM), Caddy file_server |
| 18 | Auditable Voting (nsite) | `nsite./<npub>/` | — | Nostr static site via blossom + nsyte |

## Architecture

```
Internet → Cloudflare DNS (auto A records via API)
  → VPS (Debian 13)
    → Caddy (:80/:443, Docker host network, auto HTTPS via Cloudflare DNS-01)
      ├── relay.BASE_DOMAIN     → strfry (Docker :7777)
      ├── chat.BASE_DOMAIN      → obelisk-relay (Docker :8080)
      ├── blossom.BASE_DOMAIN   → blossom-server (Docker :3001)
      ├── nsite.BASE_DOMAIN     → nsite-gateway (Docker :3002)
      ├── releases.BASE_DOMAIN  → /srv/tollgate/releases/ (Caddy file_server)
      ├── ci.BASE_DOMAIN        → /srv/tollgate/hive-ci/ (Caddy file_server)
      ├── git.BASE_DOMAIN       → ngit-grasp (Systemd :7334)
      ├── routstr.BASE_DOMAIN   → Routstr Core (Docker :8000) ← AI inference proxy
       ├── *.mints.BASE_DOMAIN   → CDK mintd containers (:8085-:8089)
       │   ├── test-mb  (:8085)
       │   ├── test-kb  (:8086)
       │   ├── test-gb  (:8087)
       │   ├── test-min (:8088)
       │   └── routstr-mint (:8089) ← dedicated mint for AI credits
       └── print.mints.BASE_DOMAIN → cashu-brrr static + /api/* proxy → mint operator proxy (:3000)

    Auditable Voting:
      ├── vote.BASE_DOMAIN        → Static React+Vite+WASM build (Caddy file_server)
      └── nsite via blossom        → Same build published to Nostr (our relay + blossom + public)

    Routstr AI Inference Node:
      ├── Routstr Core (Docker :8000)
      │     FastAPI reverse proxy for OpenAI-compatible APIs
      │     Accepts Cashu eCash payments via routstr-mint
      │     Proxies to Z.ai Coding Plan (GLM-5.1) upstream
      │     Admin dashboard at /admin/
      │     Nostr discovery (kind 38421) via local relay
      ├── Tor hidden service (Docker host network)
      │     Anonymous .onion access to Routstr API
      └── Dedicated CDK mint (routstr-mint, :8089, gRPC :50055)
            Node operator issues AI credits (sat/msat units)
            Connected to mint orchestrator for approval flow

    Mint orchestrator:
      ├── tollgate-mint-orchestrator (Python daemon :8090)
      │     Subscribes to Nostr relay for kind:38010 approval events
      │     Validates Nostr signatures + npub ownership
      │     Calls CDK gRPC UpdateNut04Quote to approve issuance
      │     Publishes confirmation events to relay
      ├── mint-approve CLI (Python, for mint owners)
      └── mint-dashboard (static HTML, client-side nsec signing)

    System services (not HTTP):
      ├── shadowsocks-libev (TCP :65101, MPTCP enabled)
      ├── glorytun (UDP :65001)
      └── fips daemon (TUN interface + nftables)

    CLI tools:
      └── nsyte (global Deno binary)
```

## CDK Fakewallet Custom Unit Bug

CDK v0.16.0 has two bugs that prevent custom units (MB, KB, GB, min) with the fakewallet:

1. **Case mismatch**: `CurrencyUnit::Custom` serializes to lowercase (`Custom("MB")` → `"mb"`) but `FromStr` preserves case. The payment processor HashMap key `Custom("MB")` doesn't match the deserialized `Custom("mb")` from requests → "No payment processor set for pair mb, bolt11".

2. **No msat conversion**: Fakewallet calls `convert_currency_amount(custom_unit, Msat)` but only knows `Sat↔Msat` and `Usd/Eur→Msat`. No path for custom units → "Could not create invoice: Unknown invoice amount".

**Workaround**: All mints use `CDK_MINTD_FAKE_WALLET_SUPPORTED_UNITS=sat`. Display unit mapping is handled in the cashu-brrr frontend (mint URL → display unit). See `cashu-brrr/HANDOVER.md` Phase 5.

**Future fix options**: gRPC payment processor, CDK fork, or upstream fix.

## Mint Orchestrator Design

### Cashu Mint (CDK mintd)

- **Docker image**: `cashubtc/mintd:latest` (official, not a fork)
- **Lightning backend**: `fakewallet` — auto-fills quotes
- **gRPC management**: `cdk-mint-rpc` built into CDK — `UpdateNut04Quote` sets quote state
- **Per-mint containers**: each unit gets its own mintd instance with unique ports
- **Active mints**: `test-mb` (sat, displayed as MB), `test-kb` (sat, displayed as KB), `test-gb` (sat, displayed as GB), `test-min` (sat, displayed as min)
- **Database**: SQLite per mint
- **Key constraint**: All mints use `sat` internally due to CDK fakewallet bug. Custom unit display is a frontend concern.

### Approval Flow (Nostr-based)

1. User creates mint quote via Cashu wallet → `POST /v1/mint/quote/bolt11`
2. Quote starts UNPAID (fakewallet auto-fills after delay, but orchestrator can gate via gRPC)
3. Mint owner signs kind 38010 Nostr event approving the quote
4. Orchestrator validates signature, calls gRPC `UpdateNut04Quote` → PAID
5. User mints tokens → `POST /v1/mint/bolt11`

### CDK gRPC (cdk-mint-rpc)

Proto: `crates/cdk-mint-rpc/src/proto/cdk-mint-rpc.proto` from `cashubtc/cdk`
- Package: `cdk_mint_management_v1`
- Key RPC: `UpdateNut04Quote(UpdateNut04QuoteRequest) → UpdateNut04QuoteRequest`
- Env vars: `CDK_MINTD_MINT_MANAGEMENT_ENABLED`, `CDK_MINTD_MANAGEMENT_PORT`

### CDK mintd Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `CDK_MINTD_URL` | Mint public URL |
| `CDK_MINTD_LN_BACKEND` | `fakewallet` for testing |
| `CDK_MINTD_LISTEN_HOST` | `0.0.0.0` in Docker |
| `CDK_MINTD_LISTEN_PORT` | REST API port |
| `CDK_MINTD_DATABASE` | `sqlite` |
| `CDK_MINTD_MNEMONIC` | Seed for key derivation |
| `CDK_MINTD_FAKE_WALLET_SUPPORTED_UNITS` | Comma-separated units |
| `CDK_MINTD_MINT_MANAGEMENT_ENABLED` | `true` to enable gRPC |
| `CDK_MINTD_MANAGEMENT_PORT` | gRPC port |
| `CDK_MINTD_LN_MIN_MINT` / `CDK_MINTD_LN_MAX_MINT` | Mint amount limits |

## Cloudflare DNS Automation

The `cloudflare_dns` Ansible role creates A records for: `relay`, `chat`, `blossom`, `nsite`, `releases`, `ci`, `git`, `routstr`, `vote`, `*.mints`

## Deployment Flow

```
make deploy  (or ./scripts/deploy.sh)
  01. System setup (packages, locale, sysctl)
  02. Docker + Compose V2 installation
  03. Cloudflare DNS record creation
  04. Caddy reverse proxy deployment
  05. strfry Nostr relay
  06. obelisk-relay NIP-29 group chat
  07. blossom-server blob storage
  08. nsite-gateway
  09. tollgate-release-explorer (static)
  10. hive-ci-site (static)
  11. Mint orchestrator + dashboard
  12. MPTCP server (Shadowsocks + Glorytun)
  13. FIPS mesh network
  14. nsyte CLI installation
  15. GRASP server (ngit-grasp)
  16. Routstr AI inference node + dedicated mint + Tor
  17. Auditable Voting (static + nsite)
  → Integration tests
  → Playwright E2E tests
```

## Testing Strategy

| Level | Tool | What it tests |
|-------|------|---------------|
| Unit | pytest | Registry, event validator, gRPC client, audit log, daemon |
| Integration | Bash + pytest | Package imports, full pytest suite, service health |
| E2E | Playwright (TypeScript) | API endpoints, dashboard UI, mint REST API, TLS |
