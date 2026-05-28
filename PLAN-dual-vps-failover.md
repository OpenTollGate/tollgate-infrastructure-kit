# PLAN-dual-vps-failover.md

## Overview

Multi-VPS deployment with automated failover. All services deploy to both VPSes with `ignore_unreachable: true` so a down VPS doesn't block the other. Syncthing replicates stateful data between VPSes and to the backup machine.

## Machines

| Label | IP | User | Password | Role |
|---|---|---|---|---|
| vps1 | `66.92.204.38` | `debian` | `churn-coyote-twin-alpha-celery-peace` | Primary (active for stateful) |
| vps2 | `23.182.128.51` | `debian` | `patrol-rigid-fire-tip-finger-index` | Secondary (standby for stateful) |
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
      │(debian) │    │(debian) │
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

### Per-VPS only

- vps1: bitcoin-core
- vps2: bitcoin-knots, micro-vpn

### Shared (both VPSes)

- jitsi-meet (`meet.orangesync.tech`)

## DNS Records

| Subdomain | Type | Records | Failover |
|---|---|---|---|
| `orangesync.tech` | A x2 | `66.92.204.38`, `23.182.128.51` | Caddy |
| `nsite` | A x2 | both IPs | Caddy |
| `chat` | A x2 | both IPs | Caddy |
| `git` | A x2 | both IPs | Caddy |
| `services` | A x2 | both IPs | Caddy |
| `routstr` | A x2 | both IPs | Caddy |
| `vote` | A x2 | both IPs | Caddy |
| `workshop` | A x2 | both IPs | Caddy |
| `releases` | A x2 | both IPs | Caddy |
| `ci` | A x2 | both IPs | Caddy |
| `runner` | A x2 | both IPs | Caddy |
| `solix` | A x2 | both IPs | Caddy |
| `wot` | A x2 | both IPs | Caddy |
| `meet` | A x2 | both IPs | Caddy |
| `relay1` | A | `66.92.204.38` | None (unique) |
| `relay2` | A | `23.182.128.51` | None (unique) |
| `ngit1` | A | `66.92.204.38` | None (unique) |
| `ngit2` | A | `23.182.128.51` | None (unique) |
| `blossom1` | A | `66.92.204.38` | None (unique) |
| `blossom2` | A | `23.182.128.51` | None (unique) |
| `*.mints` | A | `66.92.204.38` only | DNS change on failover |
| `vpn` | A | `23.182.128.51` only | None |

## Syncthing Folders (VPS-1 <-> VPS-2 <-> Backup, all sendreceive)

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

### Failover Actions (vps-1 -> vps-2)

1. SSH to vps-2, start standby services:
   - `systemctl start ngit-grasp`
   - `cd /opt/tollgate/mints/test-mb && docker compose up -d` (for each mint)
   - `cd /opt/tollgate/routstr && docker compose up -d`
   - `systemctl start tollgate-act-runner`
2. Update Cloudflare DNS: `*.mints.orangesync.tech` -> `23.182.128.51`
3. Caddy on vps-2 already handles shared services via failover upstreams
4. Mark failover active in watchdog state

### Failback (manual for now, logic in place for auto)

1. Wait for syncthing to sync latest data back to vps-1
2. Start services on vps-1
3. Stop services on vps-2 (back to standby)
4. Restore DNS: `*.mints.orangesync.tech` -> `66.92.204.38`
5. Clear failover state

Run manually: `scripts/failover.py --failback`

---

## Implementation Checklist

### Layer 1: Foundation — DONE

- [x] 1.1 Update `.env` (VPS_IP, VPS_USER, VPS_PASSWORD, VPS2_IP, VPS2_USER, VPS2_PASSWORD)
- [x] 1.2 Rewrite `ansible/inventory/hosts.yml` (vps1, vps2, backup, vps group, ConnectTimeout=15)
- [x] 1.3 Update `group_vars/m1.yml` — machine_id: vps1, machine_number: 1, machine_active: true
- [x] 1.4 Update `group_vars/m2.yml` — machine_id: vps2, machine_number: 2, machine_active: false
- [x] 1.5 Update `group_vars/all.yml` (shared_subdomains, per_machine_subdomains lists)

### Layer 2: Mechanical Playbook Updates — DONE

- [x] 2.1 `00-zram.yml` — `ignore_unreachable: true`
- [x] 2.2 All playbooks — `hosts: vps` or per-machine + `ignore_unreachable: true`
- [x] 2.3 `deploy-mint.yml` — same
- [x] 2.4 `deploy-test-mints.yml` — same

### Layer 3: Setup Playbooks — DONE

- [x] 3.1 `setup-vps-1.yml` — hosts: vps1, 28 roles, ignore_unreachable
- [x] 3.2 `setup-vps-2.yml` — hosts: vps2, 30 roles (includes micro_vpn, bitcoin_knots)
- [x] 3.3 `setup-all.yml` imports both
- [x] 3.4 `setup-http-only.yml` — `hosts: vps` + `ignore_unreachable`

### Layer 4: Active-Passive Role Modifications — DONE

- [x] 4.1 `grasp/tasks/main.yml` — guarded with `when: machine_active | default(true)`
- [x] 4.2 `routstr/tasks/main.yml` — same
- [x] 4.3 `cashu_mint/tasks/main.yml` — same
- [x] 4.4 `mint_orchestrator/tasks/main.yml` — same
- [x] 4.5 `act_runner/tasks/main.yml` — same

### Layer 5: DNS Role — DONE

- [x] 5.1 `cloudflare_dns/tasks/main.yml` — dual-A-record for shared, numbered for per-machine, `*.mints` to vps1

### Layer 6: Caddy Template — DONE

- [x] 6.1 `caddy/templates/Caddyfile.http.j2` — failover upstreams, numbered subdomains, active-passive guards

### Layer 7: Syncthing — DONE (code), NOT YET PEEERED

- [x] 7.1 `syncthing/defaults/main.yml` — expanded folders
- [x] 7.2 `21-syncthing.yml` — `hosts: vps` + `ignore_unreachable`
- [x] 7.3 `syncthing/tasks/peering-local.yml` — peer backup with both VPSes
- [x] 7.4 `syncthing/tasks/peering.yml` — hostvars references
- [ ] 7.5 Syncthing actually peered and syncing between vps1 <-> vps2 <-> backup

### Layer 8: GRASP Snapshot Role — DONE

- [x] 8.1 `ansible/roles/grasp_snapshot/tasks/main.yml`
- [x] 8.2 `ansible/roles/grasp_snapshot/templates/tollgate-grasp-snapshot.sh.j2`
- [x] 8.3 `ansible/roles/grasp_snapshot/templates/tollgate-grasp-snapshot.service.j2`
- [x] 8.4 `ansible/roles/grasp_snapshot/templates/tollgate-grasp-snapshot.timer.j2`
- [ ] 8.5 Snapshot timer active and running on both VPSes

### Layer 9: Failover Script — DONE

- [x] 9.1 `scripts/failover.py` — failover/failback with Cloudflare DNS update + service start/stop

### Layer 10: Watchdog — DONE (code)

- [x] 10.1 `scripts/watchdog.json` — dual-machine config
- [x] 10.2 `watchdog/templates/watchdog.json.j2`
- [x] 10.3 `scripts/watchdog.py` — failover detection, trigger, failback logic

### Layer 11: Dashboard + Stats — DONE

- [x] 11.1 `static/services/index.html` — vps1/vps2, new IPs, failover status
- [x] 11.2 `backup/files/gen-vps-stats.py` — unified service list
- [x] 11.3 `backup/files/gen-backup-status.py` — new syncthing config path
- [x] 11.4 `backup/tasks/main.yml` — snapshot dir

### Layer 12: Bitcoin + Jitsi — DONE (roles created)

- [x] 12.1 Bitcoin Core role — builds from source, listen=0, pruned 10GB, cgroup limits
- [x] 12.2 Bitcoin Knots role — builds from source, RDTS_CONSENT, listen=0, cgroup limits
- [x] 12.3 Jitsi Meet role — docker-jitsi-meet stable-9584, no-auth
- [x] 12.4 Bitcoin Core deployed to vps1 — IBD ~39%
- [x] 12.5 Bitcoin Knots deployed to vps2 — IBD ~12%
- [ ] 12.6 Jitsi Meet deployed to vps1
- [ ] 12.7 Jitsi Meet deployed to vps2

### Layer 13: Commit and Push — DONE

- [x] 13.1 Committed to `act-runner-tollgate-module-ci` branch
- [x] 13.2 Pushed to origin, github, orangesync

---

## Deployment Checklist (current state)

### VPS1 (66.92.204.38) — Primary

| # | Role | Status | Notes |
|---|------|--------|-------|
| 1 | system | OK | |
| 2 | docker | OK | 16 containers running |
| 3 | cloudflare_dns | OK | |
| 4 | caddy | OK | Docker, ports 80/443 |
| 5 | strfry | OK | Docker |
| 6 | obelisk_relay | OK | Docker |
| 7 | blossom | OK | Docker |
| 8 | nsite_gateway | OK | Docker |
| 9 | release_explorer | OK | |
| 10 | hive_ci | OK | ignore_errors on npm |
| 11 | mint_orchestrator | OK | |
| 12 | cashu_brrr | OK | |
| 13 | mint_operator_proxy | OK | health check accepts 401 |
| 14 | mptcp_server | OK | ignore_errors on glorytun |
| 15 | fips | OK | systemd active |
| 16 | nsyte_cli | INACTIVE | systemd inactive |
| 17 | grasp | INACTIVE | systemd inactive |
| 18 | act_runner | OK | systemd active |
| 19 | routstr | OK | Docker |
| 20 | auditable_voting | OK | |
| 21 | ngit_relay | OK | Docker |
| 22 | backup | OK | |
| 23 | gitworkshop | OK | |
| 24 | grasp_mirror | OK | |
| 25 | cloud_lab_runner | OK | |
| 26 | relatr | OK | Docker |
| 27 | jitsi_meet | NOT DEPLOYED | compose file missing |
| 28 | bitcoin_core | OK | IBD ~39%, systemd active |
| 29 | grasp_snapshot | INACTIVE | timer not running |
| 30 | syncthing | INACTIVE | systemd inactive |

### VPS2 (23.182.128.51) — Secondary

| # | Role | Status | Notes |
|---|------|--------|-------|
| 1 | system | OK | |
| 2 | docker | OK | 20 containers running |
| 3 | cloudflare_dns | OK | |
| 4 | caddy | OK | Docker, ports 80/443 |
| 5 | strfry | OK | Docker |
| 6 | obelisk_relay | OK | Docker |
| 7 | blossom | OK | Docker |
| 8 | nsite_gateway | OK | Docker |
| 9 | release_explorer | OK | |
| 10 | hive_ci | OK | |
| 11 | mint_orchestrator | OK | |
| 12 | cashu_brrr | OK | |
| 13 | mint_operator_proxy | OK | |
| 14 | mptcp_server | OK | |
| 15 | fips | OK | systemd active |
| 16 | nsyte_cli | INACTIVE | systemd inactive |
| 17 | grasp | OK | systemd active |
| 18 | grasp_snapshot | INACTIVE | timer not running |
| 19 | act_runner | OK | systemd active (5 stale containers) |
| 20 | routstr | OK | Docker |
| 21 | auditable_voting | OK | |
| 22 | ngit_relay | OK | Docker |
| 23 | backup | OK | |
| 24 | gitworkshop | OK | |
| 25 | grasp_mirror | OK | |
| 26 | cloud_lab_runner | OK | |
| 27 | relatr | OK | Docker |
| 28 | micro_vpn | BROKEN | port 5010 connection refused |
| 29 | jitsi_meet | NOT DEPLOYED | compose file missing |
| 30 | bitcoin_knots | OK | IBD ~12%, systemd active |
| 31 | syncthing | OK | systemd active |
| - | mints (3) | RESTARTING | mint-test-gb, mint-test-kb, mint-test-mb |

---

## Remaining Work Checklist

### Critical (infrastructure health)

- [ ] R1 Run `setup-vps-1.yml` end-to-end — fix all role failures until clean pass
- [ ] R2 Run `setup-vps-2.yml` end-to-end — fix all role failures until clean pass
- [ ] R3 Deploy Jitsi Meet to vps1 (role exists, compose not applied)
- [ ] R4 Deploy Jitsi Meet to vps2 (role exists, compose not applied)
- [ ] R5 Fix syncthing on vps1 (inactive) and establish peering vps1 <-> vps2 <-> backup
- [ ] R6 Fix 3 restarting mints on vps2 (mint-test-gb, mint-test-kb, mint-test-mb)

### Medium (service health)

- [ ] R7 Start ngit-grasp on vps1 (standby primary — should be active)
- [ ] R8 Start grasp_snapshot timer on both VPSes
- [ ] R9 Fix micro_vpn on vps2 (port 5010 connection refused)
- [ ] R10 Clean up stale act-runner containers on vps2 (5 containers from 44h ago)
- [ ] R11 Verify nsyte_cli on both VPSes
- [ ] R12 Test failover dry-run: `scripts/failover.py --dry-run --failover`

### Lower (polish)

- [ ] R13 Verify solix nsite deployed
- [ ] R14 Publish relay advertisement Nostr events
- [ ] R15 Voting worker dinner vote walkthrough
- [ ] R16 Update PROGRESS.md to reflect current state
