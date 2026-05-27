# PLAN-dual-vps-failover.md

## Overview

Multi-VPS deployment with automated failover. All services deploy to both VPSes with `ignore_unreachable: true` so a down VPS doesn't block the other. Syncthing replicates stateful data between VPSes and to the backup machine.

## Machines

| Label | IP | User | Password | Role |
|---|---|---|---|---|
| vps-1 | `66.92.204.38` | `root` | `churn-coyote-twin-alpha-celery-peace` | Primary (active for stateful) |
| vps-2 | `23.182.128.51` | `debian` | `patrol-rigid-fire-tip-finger-index` | Secondary (standby for stateful) |
| backup | `100.90.22.201` | `c03rad0r` | `c03rad0r123` (sudo) | Syncthing backup target |

**Abandoned**: `23.182.128.226` (unreachable, removed from all configs)

## Architecture

```
                     Cloudflare DNS
                          │
           ┌──────────────┼──────────────┐
           │              │              │
      Shared (2 A)    Per-machine (1 A)  VPS-1 only (1 A)
      nsite,chat,git   relay1 → vps-1    *.mints → vps-1
      services,vote    relay2 → vps-2
      workshop,...     ngit1 → vps-1
      routstr          ngit2 → vps-2
      orangesync.tech  blossom1 → vps-1
                       blossom2 → vps-2
           │              │
      ┌────┴────┐    ┌────┴────┐
      │  VPS-1  │    │  VPS-2  │
      │ 66.92.  │    │ 23.182. │
      │ 204.38  │    │ 128.51  │
      │ (root)  │    │(debian) │
      └────┬────┘    └────┬────┘
           │  syncthing    │
           │◄─────────────►│
           │  sendreceive  │
           └───────┬───────┘
                   │ syncthing
           ┌───────┴───────┐
           │    Backup     │
           │ 100.90.22.201 │
           └───────────────┘
```

## Service Modes

### Active-Active (running on both VPSes, Caddy failover + DNS round-robin)

caddy, nsite-gateway, obelisk (chat), releases, ci, vote, workshop, solix, wot, services dashboard, relatr, gitworkshop, nsyte, fips, mptcp-server

### Active-Passive (running on vps-1, standby on vps-2, watchdog failover)

GRASP (git), routstr, all mints, act-runner

### Unique per-VPS (independent instances, no sync)

strfry relay (relay1/relay2), ngit-relay (ngit1/ngit2), blossom (blossom1/blossom2)

### VPS-2 only

micro-vpn

## DNS Records

| Subdomain | Type | Records | Failover |
|---|---|---|---|
| `orangesync.tech` | A ×2 | `66.92.204.38`, `23.182.128.51` | Caddy |
| `nsite` | A ×2 | both IPs | Caddy |
| `chat` | A ×2 | both IPs | Caddy |
| `git` | A ×2 | both IPs | Caddy |
| `services` | A ×2 | both IPs | Caddy |
| `routstr` | A ×2 | both IPs | Caddy |
| `vote` | A ×2 | both IPs | Caddy |
| `workshop` | A ×2 | both IPs | Caddy |
| `releases` | A ×2 | both IPs | Caddy |
| `ci` | A ×2 | both IPs | Caddy |
| `runner` | A ×2 | both IPs | Caddy |
| `solix` | A ×2 | both IPs | Caddy |
| `wot` | A ×2 | both IPs | Caddy |
| `relay1` | A | `66.92.204.38` | None (unique) |
| `relay2` | A | `23.182.128.51` | None (unique) |
| `ngit1` | A | `66.92.204.38` | None (unique) |
| `ngit2` | A | `23.182.128.51` | None (unique) |
| `blossom1` | A | `66.92.204.38` | None (unique) |
| `blossom2` | A | `23.182.128.51` | None (unique) |
| `*.mints` | A | `66.92.204.38` only | DNS change on failover |
| `vpn` | A | `23.182.128.51` only | None |

## Syncthing Folders (VPS-1 ↔ VPS-2 ↔ Backup, all sendreceive)

| ID | Path (live data) | Notes |
|---|---|---|
| `orangesync-grasp` | `/opt/tollgate/snapshots/grasp/` | Via mdb_copy snapshot every 5min |
| `orangesync-mints` | `/opt/tollgate/mints/` | SQLite WAL, safe for live sync |
| `orangesync-routstr` | `/opt/tollgate/routstr/` | SQLite WAL |
| `orangesync-caddy` | `/opt/tollgate/caddy/data/` | TLS certs |
| `orangesync-act-runner` | `/opt/tollgate/act-runner/` | SQLite + artifacts |
| `orangesync-static` | `/srv/tollgate/` | Static sites |

Not synced (unique per VPS): strfry DB, ngit-relay DB, blossom DB

## GRASP Safety: mdb_copy Snapshot

- Install `lmdb-utils` on both VPSes
- Systemd timer runs every 5 minutes
- `mdb_copy /opt/tollgate/grasp/data/relay /opt/tollgate/snapshots/grasp/relay` (hot backup, no stop)
- `rsync -a --delete /opt/tollgate/grasp/data/git/ /opt/tollgate/snapshots/grasp/git/` (git repos, safe)
- Syncthing syncs from `/opt/tollgate/snapshots/grasp/` (consistent snapshot)

## Automated Failover

### Detection

VPS is "down" if SSH unreachable for 3 consecutive watchdog checks (6 min at 120s interval).

### Failover Actions (vps-1 → vps-2)

1. SSH to vps-2, start standby services:
   - `systemctl start ngit-grasp`
   - `cd /opt/tollgate/mints/test-mb && docker compose up -d` (for each mint)
   - `cd /opt/tollgate/routstr && docker compose up -d`
   - `systemctl start tollgate-act-runner`
2. Update Cloudflare DNS: `*.mints.orangesync.tech` → `23.182.128.51`
3. Caddy on vps-2 already handles shared services via failover upstreams
4. Mark failover active in watchdog state

### Failback (manual for now, logic in place for auto)

1. Wait for syncthing to sync latest data back to vps-1
2. Start services on vps-1
3. Stop services on vps-2 (back to standby)
4. Restore DNS: `*.mints.orangesync.tech` → `66.92.204.38`
5. Clear failover state

Run manually: `scripts/failover.py --failback`

---

## Implementation Checklist

### Layer 1: Foundation

- [ ] 1.1 Update `.env` (VPS_IP, VPS_USER, VPS_PASSWORD, VPS2_IP, VPS2_USER, VPS2_PASSWORD)
- [ ] 1.2 Rewrite `ansible/inventory/hosts.yml` (vps-1, vps-2, backup, vps group, ConnectTimeout=15)
- [ ] 1.3 Rename `group_vars/m1.yml` → `vps-1.yml`, update content (machine_id, machine_number, machine_ip, other_vps_ip, machine_active, full machine_roles, subdomain lists)
- [ ] 1.4 Rename `group_vars/m2.yml` → `vps-2.yml`, update content (same vars, vps-2 values, machine_active: false)
- [ ] 1.5 Update `group_vars/all.yml` (shared_subdomains, per_machine_subdomains lists)

### Layer 2: Mechanical Playbook Updates (37 files)

- [ ] 2.1 `00-zram.yml` — add `ignore_unreachable: true`
- [ ] 2.2 `01-system.yml` through `32-relatr.yml` (35 files) — `hosts: vps` + `ignore_unreachable: true` + `serial: 1`
- [ ] 2.3 `deploy-mint.yml` — same
- [ ] 2.4 `deploy-test-mints.yml` — same

### Layer 3: Setup Playbooks

- [ ] 3.1 Rename `setup-m1.yml` → `setup-vps-1.yml`, update `hosts: vps-1`, add `ignore_unreachable`, add `grasp_snapshot` role
- [ ] 3.2 Rename `setup-m2.yml` → `setup-vps-2.yml`, update `hosts: vps-2`, same full roles as vps-1
- [ ] 3.3 Update `setup-all.yml` imports
- [ ] 3.4 Update `setup-http-only.yml` — `hosts: vps` + `ignore_unreachable`

### Layer 4: Active-Passive Role Modifications

- [ ] 4.1 `grasp/tasks/main.yml` — guard service start with `when: machine_active | default(true)`
- [ ] 4.2 `routstr/tasks/main.yml` — same
- [ ] 4.3 `cashu_mint/tasks/main.yml` — same
- [ ] 4.4 `mint_orchestrator/tasks/main.yml` — same
- [ ] 4.5 `act_runner/tasks/main.yml` — same

### Layer 5: DNS Role

- [ ] 5.1 Rewrite `cloudflare_dns/tasks/main.yml` — dual-A-record for shared subdomains, numbered subdomains for per-machine, `*.mints` to vps-1 only, bare domain to both IPs

### Layer 6: Caddy Template

- [ ] 6.1 Rewrite `caddy/templates/Caddyfile.http.j2` — failover upstreams for shared services (`to localhost:PORT` + `to other_vps_ip:PORT` + `fail_duration 30s`), numbered subdomains for per-machine services (`relay{{ machine_number }}`), active-passive services guarded by `{% if machine_active %}`

### Layer 7: Syncthing

- [ ] 7.1 Update `syncthing/defaults/main.yml` — expanded folders with live data paths
- [ ] 7.2 Update `21-syncthing.yml` — `hosts: vps` + `ignore_unreachable`, multi-VPS peering
- [ ] 7.3 Update `syncthing/tasks/peering-local.yml` — peer backup with both VPSes
- [ ] 7.4 Update `syncthing/tasks/peering.yml` — update hostvars references

### Layer 8: GRASP Snapshot Role (new)

- [ ] 8.1 Create `ansible/roles/grasp_snapshot/tasks/main.yml`
- [ ] 8.2 Create `ansible/roles/grasp_snapshot/templates/tollgate-grasp-snapshot.sh.j2`
- [ ] 8.3 Create `ansible/roles/grasp_snapshot/templates/tollgate-grasp-snapshot.service.j2`
- [ ] 8.4 Create `ansible/roles/grasp_snapshot/templates/tollgate-grasp-snapshot.timer.j2`

### Layer 9: Failover Script

- [ ] 9.1 Create `scripts/failover.py` — standalone failover/failback with Cloudflare DNS update + service start/stop

### Layer 10: Watchdog

- [ ] 10.1 Update `scripts/watchdog.json` — rename m1/m2, add failover config, update URLs
- [ ] 10.2 Update `watchdog/templates/watchdog.json.j2` — same
- [ ] 10.3 Update `scripts/watchdog.py` — add failover detection, trigger, failback logic

### Layer 11: Dashboard + Stats

- [ ] 11.1 Update `static/services/index.html` — vps-1/vps-2, new IPs, failover status
- [ ] 11.2 Update `backup/files/gen-vps-stats.py` — unified service list, new machine IDs, VPS2_IP
- [ ] 11.3 Update `backup/files/gen-backup-status.py` — new syncthing config path
- [ ] 11.4 Update `backup/tasks/main.yml` — add snapshot dir

### Layer 12: Commit and Push

- [ ] 12.1 Commit all changes
- [ ] 12.2 Push to all remotes

### Testing

- [ ] 13.1 `ansible vps -m ping` (vps-2 OK, vps-1 UNREACHABLE expected)
- [ ] 13.2 `ansible-playbook setup-vps-2.yml` (deploy to reachable VPS)
- [ ] 13.3 `ansible-playbook setup-all.yml` (deploys both, skips unreachable)
