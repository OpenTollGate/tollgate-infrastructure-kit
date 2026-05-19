# PROGRESS.md

## Done

### Base Infrastructure
- [x] PLAN.md — full implementation plan
- [x] PROGRESS.md — this checklist
- [x] AGENTS.md — standing instructions
- [x] Repo structure created (12 Ansible roles, 16 playbooks, scripts, tests, docs)
- [x] System role made safe for shared VPS (opt-in destructive ops)
- [x] **strfry** deployed — `https://relay.orangesync.tech` (port 7777)
- [x] **obelisk-relay** deployed — `https://chat.orangesync.tech` (port 8080)
- [x] **blossom-server** deployed — `https://blossom.orangesync.tech` (port 3001)
- [x] **nsite-gateway** deployed — `https://nsite.orangesync.tech` (port 3002)
- [x] **tollgate-release-explorer** deployed — `https://releases.orangesync.tech`
- [x] **Caddy** deployed — reverse proxy with TLS via Cloudflare DNS-01
- [x] **Shadowsocks/MPTCP** deployed — port 65101, systemd
- [x] **Mints dashboard** deployed — `https://mints.orangesync.tech`
- [x] **Cloudflare DNS** — 9+ A records created
- [x] **TLS** — Let's Encrypt certs via Cloudflare DNS-01
- [x] **Integration tests** — 37/37 passing
- [x] **FIPS** built and installed, systemd service running
- [x] **GRASP server** deployed — `https://git.orangesync.tech` (port 7334, ngit-grasp v0.1.0)
- [x] **nsyte CLI** installed — global Deno binary in PATH

### Mint Infrastructure
- [x] **Switch from Nutshell to CDK mintd** — Docker image, gRPC proto, env vars, all 42 tests passing
- [x] **4 CDK test mints deployed** — test-mb (sat:8085), test-kb (sat:8086), test-gb (sat:8087), test-min (sat:8088)
- [x] **Cloudflare DNS** — 4 A records (DNS-only) for test-{mb,kb,gb,min}.mints.orangesync.tech
- [x] **Caddy wildcard TLS** — `*.mints.orangesync.tech` via Cloudflare DNS-01, cert valid until Aug 2026
- [x] **CDK mintd keyset ID compatibility diagnosed** — v0.16.0 uses hex IDs (`01...`), cashu-ts rc4 only accepts base64 IDs (`00...`)
- [x] **CDK mintd custom unit bug diagnosed and fixed** — Two bugs found in CDK v0.16.0:
  - `CurrencyUnit::Custom` serialization lowercases but `FromStr` preserves case → HashMap key mismatch
  - Fakewallet `convert_currency_amount()` has no path for custom units → msat conversion fails
  - **Fix**: all 4 mints switched to `sat` unit. Custom unit semantics handled via mint URL → display unit mapping in cashu-brrr UI (see HANDOVER.md Phase 5)
- [x] **All 4 mints fully functional** — bolt11 quotes created, fakewallet auto-pays within seconds, tokens can be minted
- [x] **Ansible playbook updated** — `deploy-test-mints.yml` uses `sat` for all test mints
- [x] **Mint registry** — `/opt/tollgate/mints/registry.json` with all 4 mints, units set to `sat`

### cashu-brrr Frontend + Operator Proxy
- [x] **Upgrade `@cashu/cashu-ts` to v2.9.0** — fixes hex keyset ID compatibility with CDK mintd v0.16.0. Required `@noble/curves@1.4.0` + `@noble/hashes@1.4.0`
- [x] **Add error handling** to `confirm()` in Step1.svelte — toast error instead of silent failure
- [x] **4 mint URLs added** to Step1.svelte (7 total mints listed: 4 ours + 3 public)
- [x] **cashu-brrr deployed** — `https://print.mints.orangesync.tech` (static Svelte frontend)
- [x] **Mint operator proxy deployed** — Node.js/Express systemd service, port 3000, `{"status":"ok","mintd":"connected"}`
- [x] **Proxy operator npubs** — 4 npubs configured, proxy connected to mintd
- [x] **Caddy routes** — `print.mints` static + `/api/*` proxy, `dashboard.mints`, 4 mint subdomains

### Mint Orchestrator + Dashboard
- [x] **Mint orchestrator** Python package — 7 modules, 42 unit tests passing
- [x] **Mint approve CLI** — signs and publishes kind 38010 Nostr approval events
- [x] **Mint dashboard** — web UI with client-side nsec signing
- [x] **Ansible roles** — `cashu_mint` (per-mint), `mint_orchestrator` (daemon + dashboard), `cashu_brrr` (frontend), `mint_operator_proxy` (systemd)
- [x] **Playwright E2E tests** — mint orchestrator API, dashboard, mint REST API
- [x] **Test coverage** — 108 tests (94 orchestrator + 14 CLI), ~96% business logic coverage
- [x] **REST API proxy** — Node.js/Express in cashu-brrr `server/`, 45 vitest tests passing
- [x] **HANDOVER.md** — full spec for admin mode + Phase 5 display unit mapping instructions

### VPS Watchdog + Caddy Subdomain Fix
- [x] **Watchdog script** — `scripts/watchdog.py` with health checks + auto-redeploy
- [x] **Watchdog config** — `scripts/watchdog.json` with 16 service definitions
- [x] **Systemd user service** — `tollgate-watchdog.service` running and enabled
- [x] **Watchdog Ansible role** — `ansible/roles/watchdog/` with templated config + systemd unit
- [x] **Watchdog playbook** — `ansible/playbooks/20-watchdog.yml` (localhost, connection: local)
- [x] **Caddyfile fixed** — individual subdomain blocks with DNS-01 TLS for all services
- [x] **Cloudflare DNS** — bare domain + vote + ngit A records added, all subdomains verified
- [x] **16/16 services healthy** — watchdog dry-run confirms all green

### Routstr Configuration
- [x] **Routstr deployed** — `https://routstr.orangesync.tech` (ghcr.io/routstr/proxy on :8000)
- [x] **Routstr mint deployed** — `mint-routstr-mint` on :8089, gRPC :50055, fakewallet sat/msat
- [x] **Tor hidden service** — anonymous .onion access
- [x] **Caddy route** — `routstr.orangesync.tech` → localhost:8000 with DNS-01 TLS
- [x] **Cloudflare DNS** — A record for `routstr` subdomain
- [x] **Nostr keypair** — generated and stored in `.env`
- [x] **Lightning address configured** — `TollGate@coinos.io` via admin API
- [x] **Dual mint support** — routstr-mint + `mint.minibits.cash/Bitcoin`
- [x] **Pricing configured** — 10% upstream fee, 0.5% exchange fee via admin API
- [x] **Admin API Ansible integration** — Routstr role configures all settings via `PATCH /admin/api/settings`
- [x] **ENV vars updated** — `ROUTSTR_RECEIVE_LN_ADDRESS` added to `.env` and `.env.example`

### ngit Relay (`ngit.orangesync.tech`)
- [x] **Ansible role** — `ansible/roles/ngit_relay/` (defaults, tasks, templates)
- [x] **Strfry container** — port 7778, 10MB event limit, 10MB WS frames, 5000 connections
- [x] **Playbook** — `ansible/playbooks/19-ngit-relay.yml`
- [x] **Cloudflare DNS** — A record for `ngit` subdomain
- [x] **Caddy route** — `ngit.orangesync.tech` → localhost:7778 with DNS-01 TLS
- [x] **Watchdog health check** — ngit-relay added to watchdog config
- [x] **Integration test** — `tests/integration/test_ngit_relay.sh`
- [x] **Deployed and verified** — `https://ngit.orangesync.tech` responds with strfry info page
- [x] **Added to setup-all.yml**

## Next Up

### Smoke Tests (completed)
- [x] **18/18 services up** — all return HTTP 200/404 (dashboard 404 on root, vote 404 before build)
- [x] **Mint tokens on test-mb** — 100 sat invoice → fakewallet auto-pay → mint → send (cashu CLI)
- [x] **Routstr models endpoint** — `/v1/models` returns GLM-4.5 + other models
- [x] **Routstr AI inference** — token payment fails due to cashu Python lib vs CDK keyset ID format mismatch (8-byte vs 33-byte hex). cashu-ts frontend handles this correctly.
- [x] **ngit relay WebSocket** — REQ/EOSE flow works, relay accepting connections
- [x] **Auditable voting deployed** — `https://vote.orangesync.tech` (WASM built, npm install fixed with `--ignore-scripts`, static files deployed)

### Services Status Page (`services.orangesync.tech`)
- [x] **Static HTML/CSS/JS** — `static/services/index.html`, dark theme with bitcoin orange + nostr purple
- [x] **17 services monitored** — Core, Mints, Frontend, AI, Other groups
- [x] **Smart recheck** — 60s auto-refresh for down services, no polling for up services
- [x] **Caddy route** — `services.{{ base_domain }}` with DNS-01 TLS
- [x] **Cloudflare DNS** — A record for `services` subdomain
- [x] **Ansible deploy** — Caddy role copies static file to `/srv/tollgate/services/`
- [x] **Live** — `https://services.orangesync.tech`

### Auditable Voting (`vote.orangesync.tech`)
- [x] **WASM build** — core + coordinator WASM compiled on VPS via cargo wasm-pack
- [x] **npm install** — fixed wasm-pack 404 by using `--ignore-scripts`
- [x] **Vite build** — static site built successfully
- [x] **Static deploy** — files copied to `/srv/tollgate/auditable-voting/`
- [x] **Keypair generated** — VOTING_NSEC/VOTING_NPUB stored in `/opt/tollgate/.env`
- [x] **Live** — `https://vote.orangesync.tech`
- [ ] **nsite deploy** — skipped (nsyte not installed on VPS)

### cashu-brrr Phase 5: Display Unit Mapping (in cashu-brrr repo)
- [ ] Add `MINT_DISPLAY_UNITS` map + `getDisplayUnit()` to `src/lib/utils.ts`
- [ ] Fix `getWalletWithUnit()` bug: `find((ks) => ks.unit)` → `find((ks) => ks.unit === unit)`
- [ ] Add `displayUnit` store to `stores.svelte.ts`
- [ ] Set display unit in `Step1.svelte` `confirm()` and `reprint()`
- [ ] Update `UnitSelector.svelte` to show display unit (e.g. "MB (internal: sat)")
- [ ] Update `Step2.svelte`, `Step3.svelte`, `LNInvoice.svelte` — pass `$displayUnit` instead of `$wallet.unit`
- [ ] Update `AdminStep3.svelte` — pass display unit to `issueTokens()`
- [ ] Update `operator.ts` — `issueTokens()` accepts optional `displayUnit`
- [ ] Update server `routes/operator.ts` + `services/blind-mint.ts` — use display unit in token metadata, keep `sat` for CDK API calls
- [ ] Rebuild and redeploy cashu-brrr frontend on VPS
- [ ] Smoke test full flow: connect to test-mb → see "MB" → mint tokens → print

### cashu-brrr Admin Mode Polish
- [ ] Test admin mode end-to-end on VPS (nsec auth → issue tokens → print)
- [ ] Verify NIP-07 auth works with browser extension

## Blocked / Deferred
- [ ] True custom unit support (MB, KB, GB, min in keyset) — requires gRPC payment processor or CDK upstream fix. See HANDOVER.md Appendix A.
- [ ] Build/deploy Hive CI content to `ci.orangesync.tech`
- [ ] Install `websocat` locally for full Playwright WebSocket tests
- [ ] Auditable voting nsite deploy — needs nsyte installed on VPS
- [ ] Routstr AI inference via cashu Python lib — keyset ID format mismatch (8-byte vs 33-byte hex). cashu-ts works correctly.
- [ ] Dashboard root path returns 404 — dashboard serves on a specific route, not root
