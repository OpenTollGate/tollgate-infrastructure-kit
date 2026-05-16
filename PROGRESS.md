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

## In Progress

- [ ] Deploy first test mint on VPS with CDK mintd
- [ ] Deploy mint orchestrator daemon on VPS
- [ ] End-to-end mint approval flow test on VPS

## Blocked / Pending

- [ ] Deploy first test mint on VPS with CDK mintd
- [ ] Deploy mint orchestrator daemon on VPS
- [ ] Build/deploy Hive CI content to `ci.orangesync.tech`
- [ ] Install `websocat` locally for full Playwright WebSocket tests
- [ ] End-to-end mint approval flow test on VPS (create quote → approve via CLI → mint tokens)
