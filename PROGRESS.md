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

### ACT Runner (`runner.orangesync.tech`)
- [x] **act-runner Python package** — 7 modules (config, daemon, watcher, executor, nostr_publisher, db, api)
- [x] **34 unit tests passing** — config, db, watcher, executor, nostr_publisher, api
- [x] **`ansible/roles/act_runner/`** — defaults, handlers, tasks, templates
- [x] **`ansible/playbooks/27-act-runner.yml`** — standalone playbook
- [x] **Static CI dashboard** — `static/runner/index.html`, dark theme, REST API consumer
- [x] **Caddy route** — `runner.{{ base_domain }}` → API proxy + static files
- [x] **Cloudflare DNS** — `runner` A record created
- [x] **`setup-all.yml`** — `act_runner` role added after `grasp`
- [x] **`.env.example`** — `ACT_RUNNER_NSEC`, `ACT_RUNNER_NPUB` added
- [x] **Services status page** — CI group added (Act Runner + Dashboard)
- [x] **Integration test** — `tests/integration/test_act_runner.sh` (9/9 passed)
- [x] **Plan documented** — `docs/act-runner-plan.md` + `docs/act-runner-deploy.md`
- [x] **Nostr keypair generated** — stored in `.env` and `/opt/tollgate/.env`
- [x] **Deployed and verified** — `https://runner.orangesync.tech` (API + dashboard live)
- [x] **nektos/act v0.2.77** installed on VPS
- [x] **tollgate-act-runner** systemd service running
- [x] **Add repos to allowlist** — all 31 repos from `npub12m5ex...` added to `act_runner_repos` in `group_vars/all.yml`. Polling via `localhost:7334` (GRASP HTTP), branch `master`.

### ACT Runner Custom Pipeline Support
- [x] **config.py** — added `pipeline`, `custom_command`, `trigger` fields to `RepoConfig` + YAML parsing
- [x] **watcher.py** — added `get_pr_branches()` + `trigger: pr_branch` support in `watch_repos()`
- [x] **executor.py** — added `execute_custom_command()` with `{branch}`/`{sha}` substitution
- [x] **daemon.py** — 3-tuple queue with `branch_name`, custom pipeline dispatch
- [x] **39/39 tests passing** — 5 new tests (config, watcher, executor)
- [x] **Config template** — `act-runner-config.yaml.j2` renders new fields
- [x] **group_vars/all.yml** — `market` repo configured with `pipeline: custom`, `trigger: pr_branch`
- [x] **Plan doc** — `docs/act-runner-custom-pipeline.md`
- [ ] Deploy to VPS via `27-act-runner.yml` playbook
- [ ] Push `pr/*` branch to market repo and verify end-to-end

### FIPS Mesh Hosting
- [x] **Plan doc** — `docs/fips-hosting-plan.md` with checklist
- [x] **fips.yaml.j2** — Nostr discovery enabled, advertise + dm relays, persistent identity
- [x] **Caddyfile.http.j2** — fips0 IPv6 site block with path-based routing for all services
- [x] **fips/tasks/main.yml** — firewall drop-in (`/etc/fips/fips.d/services.nft`) + nft apply
- [x] **fips/handlers/main.yml** — `reload nftables` handler added
- [x] **group_vars/all.yml** — `fips_identity_nsec`, `fips_mesh_ipv6`, `fips_mesh_http_port`, `fips_advertise_relays`, `fips_dm_relays`
- [ ] Deploy to VPS via `13-fips.yml` + `04-caddy.yml` playbooks
- [ ] Verify FIPS mesh access from another node

### Auditable Voting v0.1.63 Redeploy
- [x] **Plan doc** — `docs/auditable-voting-v0.1.62-deploy.md` with checklist
- [x] **E2E test repo** — `/home/c03rad0r/auditable-voting-tests/` (27 Playwright tests, pushed to ngit)
- [x] **voting_worker Ansible role** — build worker from source, keypair gen, systemd service
- [x] **auditable_voting_tests Ansible role** — clone from ngit, npm ci, Playwright install, run tests
- [x] **Playbooks** — `28-voting-worker.yml`, `29-auditable-voting-tests.yml`
- [x] **auditable_voting defaults** — branch updated to `v0.1.63`
- [ ] Redeploy auditable-voting via `17-auditable-voting.yml`
- [ ] Deploy worker via `28-voting-worker.yml`
- [ ] Run E2E tests via `29-auditable-voting-tests.yml`
- [ ] Walk through dinner vote interactively (5 voters, 5 private invite links)

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
- [x] **nsite deploy** — 24/24 blobs uploaded, manifest published to 4/4 relays

### 1A. Fix nsyte installation on VPS
- [x] Deno + nsyte installed via playbook `14-nsyte.yml` (nsyte v0.27.0)

### 1B. Fix dashboard root 404
- [x] Caddy route added: bare `mints.{{ base_domain }}` redirects to `dashboard.mints.{{ base_domain }}`
- [x] DNS A record added for `mints` subdomain
- [x] Caddy redeployed

### 1C. Deploy Hive CI (`ci.orangesync.tech`)
- [x] Source cloned from Nostr (`nostr://npub1hw6amg.../relay.ngit.dev/hive-ci-site`)
- [x] Built locally (Vue.js + Vite), deployed to VPS
- [x] Live at `https://ci.orangesync.tech`

### Smoke Tests
- [x] 18/18 services up
- [x] Mint tokens: 100 sat invoice → fakewallet auto-pay → PAID → mint → send
- [x] ngit relay WebSocket: REQ/EOSE confirmed
- [x] Routstr models: `/v1/models` returns GLM-4.5 etc.
- [x] Auditable voting: WASM built, deployed at `https://vote.orangesync.tech`

### 4A. Add Playwright E2E tests for missing services
- [ ] Routstr: check `/v1/models` returns model list
- [ ] Auditable voting: page loads at `vote.{{ base_domain }}`
- [ ] Services status page: page loads at `services.{{ base_domain }}`
- [ ] ngit relay: HTTP endpoint responds
- [ ] GRASP: `git.{{ base_domain }}` responds
- [ ] cashu-brrr: `print.mints.{{ base_domain }}` loads
- [ ] Run all Playwright tests and verify passing

## In Progress

### 5. Backup Infrastructure (Syncthing + strfry export)
- [x] `backup` Ansible role created — daily systemd timer at 02:00 UTC
  - [x] `ansible/roles/backup/defaults/main.yml`
  - [x] `ansible/roles/backup/tasks/main.yml`
  - [x] `ansible/roles/backup/templates/tollgate-backup.sh.j2`
  - [x] `ansible/roles/backup/templates/tollgate-backup.service.j2`
  - [x] `ansible/roles/backup/templates/tollgate-backup.timer.j2`
  - [x] `ansible/playbooks/22-backup.yml`
- [x] 6 backup components working: strfry JSONL, ngit-relay JSONL, GRASP git mirror, mint SQLite, Routstr data, Caddy certs
- [x] Staging dir `/opt/tollgate/backups/` with 7-day retention
- [x] Backup timer active and running

### 5B. Syncthing (VPS send-only + laptop receive-only)
- [x] `syncthing` Ansible role created — VPS + localhost + peering plays
  - [x] `ansible/roles/syncthing/defaults/main.yml`
  - [x] `ansible/roles/syncthing/tasks/vps.yml`
  - [x] `ansible/roles/syncthing/tasks/localhost.yml`
  - [x] `ansible/roles/syncthing/tasks/peering.yml`
  - [x] `ansible/roles/syncthing/handlers/main.yml`
  - [x] `ansible/playbooks/21-syncthing.yml`
- [x] Syncthing installed and running on VPS (`syncthing@syncthing.service`)
- [x] VPS config: GUI on 127.0.0.1:8384, global discovery disabled, local discovery enabled
- [x] VPS device ID: `XZ4W24N-XSKW6EB-RWR7KX5-2NSQZIK-GT66W7U-LA3NV7L-WHIZ7TL-IBEERAQ`
- [x] Local syncthing config updated with VPS device + 6 receive-only folders
- [ ] Syncthing peering not yet connected (needs root restart on local machine for config to take effect)

### 6. Relay Advertisement (Nostr + ngit)
- [x] `relay_advertisement` Ansible role created
  - [x] `ansible/roles/relay_advertisement/defaults/main.yml`
  - [x] `ansible/roles/relay_advertisement/tasks/main.yml`
  - [x] `ansible/playbooks/23-relay-advertisement.yml`
- [ ] Generate Nostr keypair for relay operator identity
- [ ] Publish kind:10002 relay list event
- [ ] Advertise GRASP-hosted git repos via ngit
- [ ] Verify: relay list discoverable on public relays

### 7. GitWorkshop (`workshop.orangesync.tech`)
- [x] Cloned from Nostr via ngit (`nostr://npub1543u4xsk6aztnreelappadcq9282yy2qm8q5ll9gkeza9t5dwxxqxncfg6/relay.primal.net/gitworkshop`)
- [x] Built locally with pnpm + Vite (React SPA, 39MB dist)
- [x] `gitworkshop` Ansible role created — builds locally, rsyncs dist to VPS
- [x] Playbook `ansible/playbooks/24-gitworkshop.yml`
- [x] Caddy route: `workshop.{{ base_domain }}` → static files
- [x] Cloudflare DNS: A record for `workshop`
- [x] Live at `https://workshop.orangesync.tech`

### 8. Testnut Mints
- [x] **testnut-cdk** (`testnut-cdk.mints.orangesync.tech`) — CDK v0.16.0, sat, fakewallet, port 8091
  - Keyset format: 64-char hex (new format)
- [x] **testnut-nutshell** (`testnut-nutshell.mints.orangesync.tech`) — Nutshell v0.20.0, sat, FakeWallet, port 8092
  - Keyset format: 64-char hex (new format, NOT compatible with gonuts-tollgate)
- [x] **testnut-compat** (`testnut-compat.mints.orangesync.tech`) — Nutshell v0.18.2, sat, FakeWallet, port 8093
  - Keyset format: 16-char hex with "00" prefix (old format, compatible with gonuts-tollgate)
  - Keyset ID confirmed: `000476d21553c414` (16 chars)
  - For use by `tollgate-module-basic-go` router daemon and `gonuts-tollgate` Go library
- [x] Caddy routes for all 3 testnut mints
- [x] Services status page updated with all 3 entries
- [x] Requirement documented in `docs/nutshell-test-mint-requirement.md`

### 9. nsite Gateway Wildcard Fix
- [x] Diagnosed: individual nsites fail because `*.nsite.orangesync.tech` wildcard DNS missing + Caddy only served `nsite.orangesync.tech` (not wildcard)
- [x] Cloudflare DNS: wildcard A record added for `*.nsite.orangesync.tech`
- [x] Caddy config updated: `*.nsite.orangesync.tech` wildcard block + `nsite.orangesync.tech` block (both proxy to :3002)
- [x] TLS cert obtained: `*.nsite.orangesync.tech` via Cloudflare DNS-01
- [x] Verified: individual nsites load (e.g. `npub1d88s....nsite.orangesync.tech` → HTTP 200)
- [x] Verified: status page still works at `nsite.orangesync.tech/status`

### 10. Solix C1000 BLE Bridge nsite (`solix.orangesync.tech`)
- [x] `solix_nsite` Ansible role created
  - [x] `ansible/roles/solix_nsite/defaults/main.yml` — relays, blossom servers, repo URL
  - [x] `ansible/roles/solix_nsite/tasks/main.yml` — clone, build, deploy static + nsyte + keygen
  - [x] `ansible/roles/solix_nsite/templates/nsite.config.json.j2`
- [x] Playbook `ansible/playbooks/25-solix-nsite.yml`
- [x] Added `solix` to `cloudflare_subdomains` in `group_vars/all.yml`
- [x] Caddy route: `solix.{{ base_domain }}` → static files with SPA fallback
- [x] Added to `setup-all.yml` and `watchdog.json`
- [x] Keypair auto-generated on VPS (SOLIX_NSEC/SOLIX_NPUB in /opt/tollgate/.env)
- [x] Source repo: `nostr://npub12m5exm2uk3xa674cc5r0hlyvccs5xxn7qv83ezuteefv5972nquq4j4szl/relay.ngit.dev/contextvm-anker-solix`
- [ ] Deploy and verify at `https://solix.orangesync.tech`

### Services Status Page Update
- [x] Updated to 21 services (was 17)
- [x] Added: testnut-cdk, testnut-nutshell, testnut-compat, GitWorkshop

## Separate Repo

### cashu-brrr Phase 5: Display Unit Mapping (in gandlafbtc/cashu-brrr repo)
- [ ] Upgrade frontend `@cashu/cashu-ts` from rc4 → 2.9.0 (+ `@noble/curves`, `@noble/hashes`)
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

### GRASP v1.0.2 Update
- [x] Switch repo URL to `nostr://danconwaydev.com/relay.ngit.dev/ngit-grasp`
- [x] Pin version to `v1.0.2` tag
- [x] Ansible role supports ngit URLs + version checkout
- [ ] Deploy to VPS via `15-grasp.yml`

## Deployment Queue (ordered)

1. [ ] **GRASP v1.0.2** — `ansible-playbook 15-grasp.yml` (rebuild from ngit source)
2. [ ] **ACT Runner custom pipeline** — `ansible-playbook 27-act-runner.yml` (redeploy with pipeline support)
3. [ ] **FIPS mesh hosting** — `ansible-playbook 13-fips.yml` (Nostr discovery + firewall drop-in)
4. [ ] **Caddy fips0 listener** — `ansible-playbook 04-caddy.yml` (mesh HTTP on fips0 IPv6)
5. [ ] **Auditable Voting v0.1.63** — `ansible-playbook 17-auditable-voting.yml` (rebuild from tag)
6. [ ] **Voting Worker** — `ansible-playbook 28-voting-worker.yml` (build worker from source)
7. [ ] **E2E Tests** — `ansible-playbook 29-auditable-voting-tests.yml` (27 Playwright tests)
8. [ ] **Verify FIPS mesh** — curl from another FIPS node or check `fipsctl show status`
9. [ ] **Custom pipeline E2E** — push `pr/*` branch to market repo, verify act-runner picks it up
10. [ ] **Dinner vote walkthrough** — 5 voters, 5 private invite links (manual, interactive)

## Blocked / Upstream
- [ ] True custom unit support (MB, KB, GB, min in keyset) — requires gRPC payment processor or CDK upstream fix
- [ ] Routstr AI inference via cashu Python lib — keyset ID format mismatch. Pre-built Docker image, needs upstream update or custom build
- [ ] Install `websocat` for full Playwright WebSocket tests (low priority, HTTP checks sufficient)
