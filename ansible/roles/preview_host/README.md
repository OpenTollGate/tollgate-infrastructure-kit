# preview_host

Provision a dedicated host for **Plebeian Market per-PR Docker previews**.

This role is a declarative port of the market repo's
`infra/preview-vps/provision.sh` (the script the `Preview Deploy` workflow runs
over SSH on every deploy). Use it to stand up a brand-new box; thereafter the
workflow's `Bootstrap VPS` step keeps it converged.

## What it does

- Installs Docker (`docker.io`) and Caddy (official repo), plus `git`/`python3`.
- Creates `/home/<user>/preview-infra` and `/home/<user>/previews`.
- Fetches `preview_gateway.py` and `preview_manager.py` from
  `PlebeianApp/market` at a **pinned commit**, verified by sha256.
- Writes `manager.env` (Cloudflare creds, `0600`) for closed-PR DNS cleanup.
- Installs and enables `preview-gateway.service` and
  `preview-manager.service` + `preview-manager.timer`.
- Writes `/etc/caddy/Caddyfile` with the on-demand-TLS `ask` endpoint and the
  `*.test-market.orangesync.tech` route (JSON access log for idle detection).

The legacy co-located **nsite gateway is off** by default
(`preview_host_nsite_gateway: false`): previews do not need it and its upstream
(`github.com/fiatjaf/nsite`) is no longer cloneable.

## Usage

```bash
VPS3_IP=<host-ip> \
CLOUDFLARE_API_TOKEN=<token> CLOUDFLARE_ZONE_ID=<zone-id> \
  ansible-playbook playbooks/53-preview-host.yml
```

The host is the `preview_host` group in `inventory/hosts.yml` (`hermes`,
address from `VPS3_IP`).

## Key variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `preview_host_user` | `{{ ansible_user }}` | Deploy user that owns the preview dirs. |
| `preview_host_gateway_port` | `6799` | Local port Caddy proxies preview traffic to. |
| `preview_host_site_suffix` | `test-market.orangesync.tech` | Preview subdomain suffix. |
| `preview_host_market_ref` | pinned commit | Market commit the scripts are fetched from. |
| `preview_host_gateway_sha256` / `preview_host_manager_sha256` | pinned | Integrity checks; clear to move refs. |
| `preview_host_cloudflare_api_token` / `preview_host_cloudflare_zone_id` | group_vars | Manager DNS cleanup. |
| `preview_host_nsite_gateway` | `false` | Enable the legacy nsite gateway. |

## Relationship to `provision.sh`

Keep the two in lockstep: the workflow still runs `provision.sh` on every
deploy, so a change to ports, units, or the Caddy route must land in **both**
places, or the next deploy will drift the host back.
