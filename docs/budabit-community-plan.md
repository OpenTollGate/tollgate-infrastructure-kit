# Budabit Community Platform — Deployment Plan

## Overview

Deploy Budabit (Flotilla fork) as a static SPA on `community.orangesync.tech` for TollGate Q&A, replacing the Signal group. Keep act-runner for CI/CD. Enable CI/CD pipelines UI for future use.

## Architecture

```
community.orangesync.tech (Caddy static file_server)
  → /srv/tollgate/budabit/ (SvelteKit static SPA)
  → SPA fallback: try_files {path} /index.html
  → All data via Nostr events (relays, Blossom)
  → No backend needed — pure client-side Nostr
```

## Configuration

```env
VITE_APP_URL=https://community.orangesync.tech
VITE_APP_NAME=TollGate Community
VITE_APP_ACCENT=#f7931a
VITE_APP_LOGO=https://community.orangesync.tech/logo.png
VITE_DEFAULT_COMMUNITY=<TollGate Communikey npub — TBD>
VITE_INDEXER_RELAYS=wss://relay.orangesync.tech,wss://ngit.orangesync.tech
VITE_GIT_RELAYS=wss://ngit.orangesync.tech,wss://relay.ngit.dev
VITE_DEFAULT_BLOSSOM_SERVERS=https://blossom.orangesync.tech
VITE_GIT_DEFAULT_CORS_PROXY=<TBD — CORS proxy for GRASP HTTP>
VITE_DEFAULT_PUBKEYS=<operator npubs in hex — TBD>
VITE_SIGNER_RELAYS=wss://relay.orangesync.tech,wss://ngit.orangesync.tech
FEATURE_GRASP=1
FEATURE_CICD=1
FEATURE_ALERTS=0
```

## Integration with Existing Stack

| Budabit Config | TollGate Service |
|---------------|-----------------|
| VITE_INDEXER_RELAYS | strfry (:7777) + ngit (:7778) |
| VITE_GIT_RELAYS | ngit (:7778) + relay.ngit.dev |
| VITE_DEFAULT_BLOSSOM_SERVERS | blossom (:3001) |
| VITE_GIT_DEFAULT_CORS_PROXY | GRASP (:7334) or CORS proxy |
| Community relays | Our strfry + ngit |
| Feature: GRASP | Our GRASP server (:7334) |
| Feature: CI/CD | act-runner (:8095) — kept as-is |

## Checklist

### Prerequisites (before deploy)
- [ ] Generate TollGate Communikey keypair (dedicated nsec/npub for community identity)
- [ ] Create kind 0 profile for community pubkey
- [ ] Create kind 10222 community definition event (relays, sections, write permissions)
- [ ] Publish community events to our relays
- [ ] Set BUDABIT_COMMUNITY_NPUB in .env
- [ ] Set BUDABIT_DEFAULT_PUBKEYS in .env (hex pubkeys of trusted members)

### Ansible Role
- [ ] `ansible/roles/budabit/defaults/main.yml` — vars, ports, paths, repo URL
- [ ] `ansible/roles/budabit/tasks/main.yml` — clone, submodule sync, build, deploy
- [ ] `ansible/roles/budabit/templates/env.production.j2` — Budabit .env template
- [ ] `ansible/roles/budabit/handlers/main.yml` — rebuild/redeploy handler

### Playbook
- [ ] `ansible/playbooks/32-budabit.yml` — standalone playbook

### Configuration Updates
- [ ] `ansible/inventory/group_vars/all.yml` — add `community` to cloudflare_subdomains, budabit vars
- [ ] `ansible/roles/caddy/templates/Caddyfile.http.j2` — `community.{{ base_domain }}` route with SPA fallback
- [ ] `.env.example` — add BUDABIT_* section
- [ ] `ansible/playbooks/setup-all.yml` — add budabit role

### Services Dashboard
- [ ] `static/services/index.html` — add Budabit (Community) entry

### CI/CD
- [x] Keep act-runner as-is — no changes needed
- [x] FEATURE_CICD=1 enables pipelines UI for future use

### Documentation
- [ ] Update PROGRESS.md with Budabit section
- [ ] Update PLAN.md services table

### Deploy & Verify
- [ ] Run `32-budabit.yml` playbook on VPS
- [ ] Verify `https://community.orangesync.tech` loads
- [ ] Verify SPA fallback works (deep links like /settings, /git/...)
- [ ] Verify relay connections from browser
- [ ] Verify Blossom uploads work
- [ ] Create TollGate community and test Q&A

## Build Process

Budabit is built from source on the VPS:
1. Clone `https://github.com/Pleb5/flotilla-budabit.git`
2. `git submodule sync --recursive && git submodule update --init --recursive`
3. `pnpm install`
4. Configure `.env` from template
5. `pnpm run build-in-production` (wraps full production build)
6. Copy `build/` to `/srv/tollgate/budabit/`
7. Caddy serves static files with SPA fallback

## Notes

- Budabit is a static SPA — no Docker container, no systemd service
- All state lives in Nostr events on our relays
- Media uploads go to our Blossom server
- Git operations use our GRASP server (needs CORS proxy or direct HTTP)
- Community identity is a Nostr pubkey, not tied to deployment
- Updates: `git pull --rebase`, submodule sync, rebuild, copy build/
