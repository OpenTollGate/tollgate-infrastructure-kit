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

## Next Up

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

## Auditable Voting Deployment

- [ ] **Ansible role** — `ansible/roles/auditable_voting/` (defaults, tasks, templates)
- [ ] **Playbook** — `ansible/playbooks/17-auditable-voting.yml`
- [ ] **Clone and build** — `tidley/auditable-voting` static site (React + Vite + WASM)
- [ ] **Static deployment** — `/srv/tollgate/auditable-voting/` served by Caddy at `vote.orangesync.tech`
- [ ] **Caddy route** — `vote.BASE_DOMAIN` with TLS via Cloudflare DNS-01
- [ ] **Cloudflare DNS** — A record for `vote` subdomain (DNS-only)
- [ ] **Nsite config** — `.nsite/config.json` with our relay + blossom + public relays/servers
- [ ] **Nsite keypair** — generate dedicated nsec/npub, store in `.env`
- [ ] **Nsite deployment** — `nsyte deploy` using our blossom + relay
- [ ] **Integration tests** — `tests/integration/test_auditable_voting.sh` (6 tests)
- [ ] Smoke test: `https://vote.orangesync.tech` loads, nsite accessible via gateway

## Routstr Node Deployment (future)
- [ ] **Routstr Ansible role** — `ansible/roles/routstr/` (defaults, tasks, templates, handlers)
- [ ] **Routstr playbook** — `ansible/playbooks/18-routstr.yml`
- [ ] **Dedicated routstr-mint** — CDK mintd container on :8089, gRPC :50055, units sat/msat
- [ ] **Routstr Core container** — ghcr.io/routstr/proxy on :8000, upstream Z.ai GLM-5.1
- [ ] **Tor hidden service** — anonymous .onion access
- [ ] **Caddy route** — `routstr.BASE_DOMAIN` → localhost:8000 with TLS
- [ ] **Cloudflare DNS** — A record for `routstr` subdomain
- [ ] **Nostr keypair** — auto-generated, persisted to `/opt/tollgate/routstr/routstr.conf`
- [ ] **Secrets in .env** — ROUTSTR_ADMIN_PASSWORD, ROUTSTR_UPSTREAM_API_KEY, etc.
- [ ] **Integration tests** — `tests/integration/test_routstr.sh`
- [ ] Smoke test: Routstr API responding, admin dashboard accessible, mint connected
