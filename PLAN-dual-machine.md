# Dual-Machine Architecture + VPS Stats + DNS Fix

## Phase 0: Finish VPS Stats UI (in progress)

- [ ] 0a Add `fetchVpsStats()` + `renderVpsStats()` JS to `static/services/index.html`
- [ ] 0b Test VPS stats rendering locally

## Phase 1: Deploy Current Changes to Active VPS (51)

- [ ] 1a Verify SSH connectivity to 23.182.128.51
- [ ] 1b Deploy backup fixes (status timer + rsync + error isolation)
- [ ] 1c Deploy Relatr to VPS 51
- [ ] 1d Deploy updated services dashboard (Micro VPN, Plebeian, Relatr, VPS stats)
- [ ] 1e Verify backup-status.json updates every minute
- [ ] 1f Verify vps-stats.json updates every 10 seconds
- [ ] 1g Verify all existing services still healthy after deploy

## Phase 2: Dual-Machine Inventory + Config

- [ ] 2a Add `machine_id` host var (m1/m2) to `ansible/inventory/hosts.yml`
- [ ] 2b Create `ansible/inventory/group_vars/m1.yml` — machine 1 specific vars
- [ ] 2c Create `ansible/inventory/group_vars/m2.yml` — machine 2 specific vars
- [ ] 2d Add `machine_domain` variable (`m1.orangesync.tech` / `m2.orangesync.tech`)
- [ ] 2e Add `base_domain` override per machine
- [ ] 2f Define service split: which roles deploy on which machine

## Phase 3: Caddy + DNS for Dual-Machine

- [ ] 3a Update Caddyfile template to generate `{{ service }}.{{ machine_domain }}` routes
- [ ] 3b Add `*.m1.orangesync.tech` Cloudflare DNS wildcard → 23.182.128.226
- [ ] 3c Add `*.m2.orangesync.tech` Cloudflare DNS wildcard → 23.182.128.51
- [ ] 3d Keep bare subdomains pointing to m1 (or active machine)
- [ ] 3e Add `m1.orangesync.tech` and `m2.orangesync.tech` landing pages

## Phase 4: Dual-Machine Playbooks

- [ ] 4a Create `ansible/playbooks/setup-m1.yml` — deploys m1 services
- [ ] 4b Create `ansible/playbooks/setup-m2.yml` — deploys m2 services
- [ ] 4c Update `setup-all.yml` to include both or be machine-aware
- [ ] 4d Ensure idempotent: re-running on already-deployed machine is safe

## Phase 5: Services Dashboard for Both Machines

- [ ] 5a Update services page to show both machines' stats side-by-side
- [ ] 5b Fetch vps-stats.json from both m1 and m2
- [ ] 5b Add machine selector or combined view
- [ ] 5c Update backup status to show cross-machine sync

## Phase 6: Deploy to Both Machines

- [ ] 6a Deploy m1 config to 23.182.128.226 (when reachable)
- [ ] 6b Deploy m2 config to 23.182.128.51
- [ ] 6c Verify both Caddy instances serve their subdomains
- [ ] 6d Verify DNS resolves correctly for m1.* and m2.* subdomains
- [ ] 6e Verify cross-machine Syncthing backup sync

## Service Split

| Service | m1 (226) | m2 (51) |
|---------|----------|---------|
| Caddy | yes | yes |
| strfry | yes | yes |
| GRASP | primary | mirror |
| Cashu mints | yes | - |
| Routstr | yes | - |
| Relatr | yes | - |
| Micro VPN | - | yes |
| ngit relay | yes | yes |
| Syncthing | yes | yes |
| Backup | yes | yes |
| Watchdog | yes | yes |
| Act Runner | yes | - |
| Blossom | yes | - |
| Obelisk | yes | - |
| Nsite Gateway | yes | - |

## Key Decisions

- Bare subdomains (relay.orangesync.tech) point to m1
- m1 = 23.182.128.226, m2 = 23.182.128.51
- Both machines run Caddy + Syncthing for cross-backup
- VPS stats update every 10 seconds
- Backup status updates every 60 seconds
- GRASP archive_all: false on both machines
