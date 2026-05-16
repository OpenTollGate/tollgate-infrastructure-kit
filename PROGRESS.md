# PROGRESS.md

## Done

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
- [x] **Cloudflare DNS** — 9 A records created
- [x] **TLS** — 9 Let's Encrypt certs via Cloudflare DNS-01
- [x] **Integration tests** — 37/37 passing
- [x] **FIPS** built and installed, systemd service running
- [x] **GRASP server** deployed — `https://git.orangesync.tech` (port 7334, ngit-grasp v0.1.0)
- [x] GRASP DNS record created, TLS cert issued
- [x] **Mint orchestrator** Python package — 7 modules, 42 unit tests passing
- [x] **Mint approve CLI** — signs and publishes kind 38010 Nostr approval events
- [x] **Mint dashboard** — web UI with client-side nsec signing
- [x] **Ansible roles** — `cashu_mint` (per-mint deployment) + `mint_orchestrator` (daemon + dashboard)
- [x] **Playwright E2E tests** — mint orchestrator API, dashboard, mint REST API
- [x] **Switch from Nutshell to CDK mintd** — Docker image, gRPC proto, env vars, all 42 tests passing
- [x] AGENTS.md — standing instructions (commit on test pass, no comments, no secrets, etc.)
- [x] PROGRESS.md — this checklist
- [x] PLAN.md updated for CDK architecture

- [x] **Test coverage** — 108 tests (94 orchestrator + 14 CLI), ~96% business logic coverage
- [x] HANDOVER.md written for cashu-brrr mint operator mode
- [x] **REST API proxy** — Node.js/Express in cashu-brrr `server/`, 45 vitest tests passing
- [x] **Ansible roles** — `cashu_brrr` (frontend build + deploy), `mint_operator_proxy` (systemd + caddy)
- [x] **mint_orchestrator role** — activated (removed `when: false`), pip venv install
- [x] **Caddyfile template** — updated with `print.mints` domain + `/api/*` proxy route
- [x] **Integration test script** — updated to run all new test files
- [x] **cashu-brrr deployed to VPS** — `https://print.mints.orangesync.tech` (static frontend)
- [x] **mint operator proxy deployed to VPS** — systemd service, port 3000, `/api/health` responding
- [x] **Caddy routes added** — `print.mints` and `dashboard.mints` on port 80 (Cloudflare proxy mode)
- [x] **Server code rsynced** — local cashu-brrr/server/ deployed to VPS (not in upstream repo)

## In Progress

- [ ] Fix cashu_mint Ansible role (mint_name override, single unit, Caddy :80)
- [ ] Create deploy-test-mints.yml playbook for 4 mints (MB, KB, GB, min)
- [ ] Create Cloudflare DNS records for test-mb, test-kb, test-gb, test-min
- [ ] Deploy 4 CDK mintd containers on VPS
- [ ] Add Caddy routes for 4 mints on VPS
- [ ] Add 4 mint URLs to cashu-brrr Step1.svelte
- [ ] Update proxy OPERATOR_NPUBS on VPS (4 operator npubs)
- [ ] Rebuild + redeploy cashu-brrr frontend
- [ ] Smoke test all mints + cashu-brrr UI
- [ ] Deploy mint orchestrator daemon on VPS
- [ ] End-to-end mint approval flow test on VPS

## Blocked / Pending

- [ ] Frontend admin mode in cashu-brrr (HANDOVER.md has full spec)
- [ ] Build/deploy Hive CI content to `ci.orangesync.tech`
- [ ] Install `websocat` locally for full Playwright WebSocket tests
