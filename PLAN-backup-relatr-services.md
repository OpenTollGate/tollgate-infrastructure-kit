# Infrastructure Fixes: Backup, GRASP Storage, Relatr WoT, Services Dashboard

## Part 1: Backup Status — Per-Minute Updates + Fine-Grained View

- [ ] 1a Create `tollgate-backup-status.service.j2` — systemd oneshot running `gen-backup-status.py`
- [ ] 1b Create `tollgate-backup-status.timer.j2` — `OnCalendar=minutely`
- [ ] 1c Add tasks to deploy + enable new timer in `backup/tasks/main.yml`
- [ ] 1d Add error fallback to `gen-backup-status.py` — write error state instead of stale JSON
- [ ] 1e Add per-folder disk usage to `gen-backup-status.py`
- [ ] 1f Auto-expand backup detail section in `static/services/index.html`

## Part 2: GRASP Storage Fix

- [ ] 2a Set `grasp_archive_all: false` in `group_vars/all.yml`
- [ ] 2b Set `grasp_archive_read_only: false` in `group_vars/all.yml`
- [ ] 2c Replace `cp -a` with `rsync --link-dest` in `tollgate-backup.sh.j2`
- [ ] 2d Add error isolation per backup section in `tollgate-backup.sh.j2`
- [ ] 2e Move status gen call to beginning of backup script

## Part 3: Deploy Relatr (WoT Trust Score Service)

- [ ] 3a Create `ansible/roles/relatr/defaults/main.yml`
- [ ] 3b Create `ansible/roles/relatr/tasks/main.yml`
- [ ] 3c Create `ansible/roles/relatr/templates/docker-compose.relatr.yml.j2`
- [ ] 3d Create `ansible/playbooks/31-relatr.yml`
- [ ] 3e Add `relatr` to `setup-all.yml`
- [ ] 3f Add `wot` subdomain Caddy route
- [ ] 3g Add `wot` to `cloudflare_subdomains` in `group_vars/all.yml`
- [ ] 3h Add relatr config vars to `group_vars/all.yml`
- [ ] 3i Create `scripts/strfry-wot-policy.sh`
- [ ] 3j Create `scripts/grasp-trust-filter.sh`
- [ ] 3k Configure strfry ngit relay write-policy
- [ ] 3l Add Relatr to watchdog

## Part 4: Services Dashboard

- [ ] 4a Add Micro VPN to SERVICES array
- [ ] 4b Add Plebeian Market E2E to SERVICES array
- [ ] 4c Add Relatr (WoT) to SERVICES array
- [ ] 4d Add `vpn` + `wot` to `cloudflare_subdomains`
- [ ] 4e Add `"51820"` to `firewall_allowed_ports`

## Execution Order

1. Parts 1+2 (backup fixes — stops bleeding)
2. Part 3 (Relatr — WoT foundation)
3. Part 4 (services page — cosmetic)
4. Commit + push after each part
5. Deploy via `ansible-playbook setup-all.yml`

## Key Config

| Variable | Value |
|----------|-------|
| Relatr root of trust | `npub1c03rad0r6q833vh57kyd3ndu2jry30nkr0wepqfpsm05vq7he25slryrnw` |
| Number of hops | 2 |
| Trust threshold | 0.1 |
| Relatr port | 3000 |
| Relatr domain | `wot.orangesync.tech` |
| Micro VPN domain | `vpn.orangesync.tech` |
| Status timer interval | Every 60 seconds |
| GRASP archive | false (only push-accepted repos) |
