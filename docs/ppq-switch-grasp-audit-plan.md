# PPQ Switch + Grasp Audit Service — Implementation Plan

## Overview

Three changes on `feat/relatr-wot-vision` branch:
1. Switch Routstr Vision upstream from OpenRouter to ppq.ai (PayPerQ)
2. Auto-generate Relatr keys in Ansible if not set in `.env`
3. Deploy `grasp-audit.py` as a systemd timer with Nostr DM reporting to c03rad0r

## 1. Switch Routstr Vision to ppq.ai

- **Base URL:** `https://api.ppq.ai/v1` (OpenAI-compatible)
- **API key:** stored in `.env` (gitignored)

### Files

- [x] `ansible/roles/routstr_vision/tasks/main.yml:49` — default → `https://api.ppq.ai/v1`
- [x] `.env.example:41,43-44` — update comment + defaults for ppq.ai

## 2. Auto-generate Relatr Keys

Replaced the `Validate Relatr configuration` assert block with a keygen block that:
1. Checks `/opt/tollgate/.env` for existing `RELATR_SERVER_SECRET_KEY` — generates via `openssl rand -hex 32` if missing
2. Checks for `RELATR_SOURCE_NPUB_HEX` — generates Nostr keypair via nacl+pynostr if missing, derives hex pubkey
3. Appends both to `/opt/tollgate/.env`

Uses Ed25519 key derivation (not SHA-256), following the fix from commit `81bc548e`.

### Files

- [x] `ansible/roles/relatr/tasks/main.yml` — replace assert with keygen block
- [x] `.env.example:51-52` — update comments to note auto-generated

## 3. Grasp Audit Service with Nostr DM Reporting

### New Ansible Role: `grasp_audit`

- [x] `ansible/roles/grasp_audit/defaults/main.yml` — vars: schedule, recipient npub, relays, data dirs
- [x] `ansible/roles/grasp_audit/tasks/main.yml` — install pynostr, deploy script, generate keypair, deploy service+timer
- [x] `ansible/roles/grasp_audit/templates/grasp-audit.service.j2` — systemd oneshot
- [x] `ansible/roles/grasp_audit/templates/grasp-audit.timer.j2` — daily at 03:00 UTC
- [x] `ansible/playbooks/33-grasp-audit.yml` — standalone playbook

### Enhanced `scripts/grasp-audit.py`

- [x] Add `--dm` flag and `send_dm()` function using pynostr
- [x] Send NIP-04 kind 4 encrypted DM to `npub1c03rad0r6q833vh57kyd3ndu2jry30nkr0wepqfpsm05vq7he25slryrnw`
- [x] DM content: audit summary (total repos, disk, top npubs, threshold breaches)
- [x] Sender keypair auto-generated as `GRASP_AUDIT_NSEC`/`GRASP_AUDIT_NPUB`

### Other Updates

- [x] `ansible/playbooks/setup-all.yml` — add `grasp_audit` role after `relatr`
- [x] `.env.example` — add `GRASP_AUDIT_*` vars
- [x] `PROGRESS.md` — update
- [x] `PLAN.md` — update

### DM Format

```
GRASP Audit Report — 2026-05-27
Total repos: 42 (1.2 GB)

Top npubs:
  npub1abc...  12 repos  450 MB
  npub1def...   8 repos  200 MB

Disk threshold breaches (>{threshold} MB): 0
```

## Key Details

- ppq.ai base URL: `https://api.ppq.ai/v1`
- API key stored only in `.env` (gitignored)
- Audit DM recipient: `npub1c03rad0r6q833vh57kyd3ndu2jry30nkr0wepqfpsm05vq7he25slryrnw`
- Audit sender keypair: auto-generated (Ed25519), same pattern as voting/worker roles
