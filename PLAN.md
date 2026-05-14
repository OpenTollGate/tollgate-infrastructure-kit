# Tollgate Infrastructure Kit — Implementation Plan

## Overview

A single Ansible-based repository that deploys all Tollgate-related infrastructure services on a single VPS with one command. Designed for anyone to run Tollgate infrastructure without depending on a small set of operators.

## Target Environment

- **OS**: Debian 13 (trixie) x86_64
- **Access**: SSH key-based (`debian@<VPS_IP>`)
- **Domain**: User brings their own (`BASE_DOMAIN` variable)
- **Secrets**: `.env` file (not committed to git)

## Services (11 total)

| # | Service | Subdomain | Internal Port | Install Method |
|---|---------|-----------|---------------|----------------|
| 1 | Caddy (reverse proxy) | gateway | 80/443 | Docker + xcaddy (with cloudflare plugin) |
| 2 | strfry (general Nostr relay) | `relay.` | 7777 | Docker |
| 3 | obelisk-relay (NIP-29 group chat) | `chat.` | 8080 | Docker (GHCR prebuilt) |
| 4 | blossom-server (blob storage) | `blossom.` | 3001 | Docker (build from hzrd149/blossom-server) |
| 5 | nsite-gateway (Nostr site gateway) | `nsite.` | 3002 | Docker (build from hzrd149/nsite-gateway) |
| 6 | tollgate-release-explorer | `releases.` | — | Static build, Caddy file_server |
| 7 | hive-ci-site | `ci.` | — | Static build, Caddy file_server |
| 8 | tg-mint-orchestrator (Cashu mints) | `*.mints.` | 8085+ | Docker per-mint, Caddy routes |
| 9 | tg-mptcp-server (MPTCP) | none | 65101/65001 | Systemd |
| 10 | FIPS (mesh network) | none | TUN | Systemd (Debian package) |
| 11 | nsyte CLI | N/A | N/A | Deno binary in PATH |

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
      └── *.mints.BASE_DOMAIN   → mint containers (Docker :8085, :8086, ...)

    System services (not HTTP):
      ├── shadowsocks-libev (TCP :65101, MPTCP enabled)
      ├── glorytun (UDP :65001)
      └── fips daemon (TUN interface + nftables)

    CLI tools:
      └── nsyte (global Deno binary)
```

## Key Decisions

- **Single proxy**: Caddy (not Traefik) — serves static files natively, simpler config, automatic HTTPS
- **Caddy deployment**: Docker with host network mode, custom build with `caddy-dns/cloudflare` plugin
- **Cloudflare**: Full automation — creates individual A records for each subdomain via API, plus DNS-01 TLS challenge
- **Blossom server**: hzrd149/blossom-server (reference implementation by protocol author)
- **Chatty relay**: obelisk-app/obelisk-relay (NIP-29, Docker, admin UI)
- **General relay**: strfry (C++, high-performance, production-grade)
- **Mint routing**: Ansible-managed Caddyfile entries with `caddy reload` per mint deployment
- **FIPS**: Full installation including kernel TUN/nftables

## Cloudflare DNS Automation

The `cloudflare_dns` Ansible role:
1. Authenticates with Cloudflare API using `CLOUDFLARE_API_TOKEN`
2. Looks up zone ID for `BASE_DOMAIN`
3. Creates/updates A records for: `relay`, `chat`, `blossom`, `nsite`, `releases`, `ci`, `*.mints`
4. All pointing at `VPS_IP`

Required secrets:
- `CLOUDFLARE_API_TOKEN` — Zone:DNS:Edit + Zone:Zone:Read
- `BASE_DOMAIN` — the user's domain

## Per-Mint Routing

When deploying a new Cashu mint:
1. `./scripts/deploy-mint.sh <npub>` runs an Ansible playbook
2. The playbook creates a new mint container on a unique port (8085, 8086, ...)
3. Appends a `handle` block to the Caddyfile for the mint's subdomain
4. Runs `caddy reload` (graceful, zero downtime)

## Deployment Flow

```
make deploy  (or ./scripts/deploy.sh)
  01. System setup (packages, locale, firewall, sysctl, users)
  02. Docker + Compose V2 installation
  03. Cloudflare DNS record creation
  04. Caddy reverse proxy deployment
  05. strfry Nostr relay
  06. obelisk-relay NIP-29 group chat
  07. blossom-server blob storage
  08. nsite-gateway
  09. tollgate-release-explorer (static)
  10. hive-ci-site (static)
  11. Cashu mint infrastructure
  12. MPTCP server (Shadowsocks + Glorytun)
  13. FIPS mesh network
  14. nsyte CLI installation
  → Integration tests
  → Playwright E2E tests
```

## Testing Strategy

| Level | Tool | What it tests |
|-------|------|---------------|
| Unit | Molecule + testinfra | Ansible role idempotency, package/service/config verification |
| Integration | Bash scripts | Health endpoints, DNS resolution, port connectivity, WebSocket, inter-service |
| E2E | Playwright (TypeScript) | Full browser tests: UI loads, WebSocket connections, API responses, TLS certs |

## Repository Structure

```
tollgate-infrastructure-kit/
├── PLAN.md
├── README.md
├── .env.example
├── .gitignore
├── Makefile
├── ansible/
│   ├── ansible.cfg
│   ├── inventory/
│   │   └── hosts.yml
│   ├── group_vars/
│   │   └── all.yml
│   ├── playbooks/
│   │   ├── setup-all.yml
│   │   ├── 01-system.yml
│   │   ├── 02-docker.yml
│   │   ├── 03-cloudflare-dns.yml
│   │   ├── 04-caddy.yml
│   │   ├── 05-strfry.yml
│   │   ├── 06-obelisk-relay.yml
│   │   ├── 07-blossom.yml
│   │   ├── 08-nsite-gateway.yml
│   │   ├── 09-release-explorer.yml
│   │   ├── 10-hive-ci-site.yml
│   │   ├── 11-mint-orchestrator.yml
│   │   ├── 12-mptcp-server.yml
│   │   ├── 13-fips.yml
│   │   └── 14-nsyte.yml
│   └── roles/
│       ├── system/
│       ├── docker/
│       ├── cloudflare_dns/
│       ├── caddy/
│       ├── strfry/
│       ├── obelisk_relay/
│       ├── blossom/
│       ├── nsite_gateway/
│       ├── release_explorer/
│       ├── hive_ci/
│       ├── mint_orchestrator/
│       ├── mptcp_server/
│       ├── fips/
│       └── nsyte_cli/
├── scripts/
│   ├── deploy.sh
│   ├── deploy-mint.sh
│   ├── remove-mint.sh
│   ├── teardown.sh
│   └── test.sh
├── tests/
│   ├── integration/
│   │   ├── test_services.sh
│   │   ├── test_dns.sh
│   │   └── test_connectivity.sh
│   └── e2e/
│       ├── playwright.config.ts
│       ├── package.json
│       └── tests/
│           ├── relay.spec.ts
│           ├── chat.spec.ts
│           ├── blossom.spec.ts
│           ├── nsite.spec.ts
│           ├── releases.spec.ts
│           ├── mint.spec.ts
│           └── tls.spec.ts
└── docs/
    ├── getting-started.md
    ├── configuration.md
    ├── services.md
    ├── adding-services.md
    ├── cloudflare-setup.md
    └── troubleshooting.md
```

## Source Repositories

| Service | Repository |
|---------|-----------|
| Tollgate Release Explorer | `git@github.com:OpenTollGate/tollgate-release-explorer-site.git` |
| TG MPTCP Server | `https://github.com/Rits1272/tg-mptcp-server.git` |
| TG Mint Orchestrator | `https://github.com/Rits1272/tg-mint-orchestrator.git` |
| Blossom Server | `https://github.com/hzrd149/blossom-server.git` |
| NSite Gateway | `https://github.com/hzrd149/nsite-gateway.git` |
| Obelisk Relay (NIP-29) | `https://github.com/obelisk-app/obelisk-relay.git` |
| strfry (Nostr relay) | `https://github.com/hoytech/strfry.git` |
| FIPS (mesh network) | `https://github.com/jmcorgan/fips.git` |
| nsyte CLI | `https://github.com/sandwichfarm/nsyte.git` |
| Hive CI Site | GitHub mirror: `https://github.com/Origami74/hive-ci-site-mirror.git` |
