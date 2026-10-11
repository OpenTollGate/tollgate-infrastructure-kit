# Dual-hosted Services PWA (cashu.me fork)

Kanban: `t_53d7a46d`. Owns the **hosting + DNS + IaC** half of the Services
surface. The Services tab UI itself is `t_55415198` (worker-layout,
`wt/cashu-services-ui`) — this work does not touch it.

## What is delivered

One installable PWA, published from **one build artifact** to **two hosts**:

| Host | URL | Serves | Status |
|------|-----|--------|--------|
| GitHub Pages | `https://pwa.orangesync.tech` | the artifact (root base path) | live |
| VPS `vps2` (Caddy) | `https://pwa-vps.orangesync.tech` | the *same* artifact | IaC merged, install leg gated on SSH |

Why `pwa.` / `pwa-vps.` and not `services.`: `services.orangesync.tech` is the
existing status page, `cvm.` is the registry (vps3), `wallet.` is an existing
vhost, and `nsite.`/`chat.`/`git.`/`relay2.`/`ngit2.`/`blossom2.`/`meet.`/
`vote.`/`ci.` are all taken. There is a `*.orangesync.tech` wildcard A record to
vps2, so both names have to be *explicit* records to have any meaning.

## One artifact, not two builds

`.github/workflows/pwa-pages.yml` in `felixfelix-bot/cashu.me`:

1. builds the PWA once (`npm run build:pwa`, `PUBLIC_PATH=/`),
2. asserts the output is installable at a domain root (`index.html`, `sw.js`,
   a manifest, no absolute `/cashu.me/` asset paths),
3. packages `dist-pwa.tar.gz` + `dist-pwa.tar.gz.sha256`,
4. deploys that exact `dist/` to GitHub Pages, **and**
5. publishes the identical `dist-pwa.tar.gz` as the rolling release asset
   `felixfelix-bot/cashu.me`:`pwa-dist-latest`.

The VPS leg (`ansible/roles/cashu_pwa`) downloads that release asset and
verifies the published sha256, so both hosts serve the same bytes and the VPS
never builds anything.

Nothing may differ between hosts except `PUBLIC_PATH` and the injected endpoint
values (`CVM_CATALOG_URL`, `CVM_RELAYS`, `CVM_NAMESPACE`,
`SERVICES_DEPLOY_TARGET`) — all injected at build time in
`quasar.config.js` / `src/js/services-endpoints.ts`. The code is never forked.

## Usage

```bash
# --- fork side (felixfelix-bot/cashu.me) --------------------------------
make pwa-build          # local PWA build (PUBLIC_PATH=/ by default)
make pwa-artifact       # dist-pwa.tar.gz + sha256 (the bytes both hosts serve)
make pwa-pages          # trigger + watch the publish workflow on main
make pwa-verify         # read the live state back from both URLs

# --- infrastructure side (this repo) -----------------------------------
make pwa-syntax         # ansible --syntax-check both playbooks
make pwa-dns            # Cloudflare: pwa CNAME -> Pages, pwa-vps A -> vps2
make pwa-deploy         # install artifact on vps2 + render Caddy vhost (SSH)
make pwa-verify         # curl both hostnames
```

`ENV_FILE` (default `./.env`) must supply `BASE_DOMAIN`, `VPS2_IP` and
`CLOUDFLARE_API_TOKEN`.

## DNS (IaC)

Declared once in `ansible/inventory/group_vars/all.yml`
(`cashu_pwa_dns_records`) and applied by role `cashu_pwa_dns`
(playbook `53-cashu-pwa-dns.yml`, runs on `localhost`). The role must never be
trusted to have worked because it returned 0: it re-reads each name from the
Cloudflare API and asserts type + content + `proxied=false`.

Records are **not** proxied: GitHub Pages cannot complete ACME through the
Cloudflare proxy, and Caddy on vps2 issues its own certificate via the
Cloudflare DNS-01 challenge.

## Serving on the VPS

Role `cashu_pwa` (playbook `53-cashu-pwa.yml`, `hosts: vps2`):

* checksum-verified download of the release artifact,
* unpack into `/srv/tollgate/pwa`,
* asserts `index.html`, `sw.js` and `manifest.webmanifest` are present and
  non-empty, and stamps `.artifact.json` with the sha256 that was installed,
* Caddy vhost `pwa-vps.<base_domain>` in
  `ansible/roles/caddy/templates/Caddyfile.http.j2`, rendered only when
  `cashu_pwa` is in the machine's `machine_roles` (it is, for `m2`/`vps2`).
  The vhost is `root /srv/tollgate/pwa` + `file_server` + SPA fallback
  (`try_files {path} /index.html` — the app uses history-mode routing) and
  sends `sw.js` with `Cache-Control: no-cache`.

## What has NOT been executed

* The VPS install leg: everything behind `pwa-deploy`. SSH to
  `23.182.128.0/24` is unreachable (`t_8eb57e3a`), so no post-state was read
  back from a live node for `ansible/roles/cashu_pwa`. Per IaC gate 6 that leg
  is **not** claimed as done.
* Separately observed while probing: TLS to vps2 currently fails for existing
  vhosts (`wallet.`, `services.` → `tlsv1 alert internal error`), i.e. Caddy on
  vps2 is not completing handshakes today. The `pwa-vps` vhost will need that
  certificate problem fixed before it can serve HTTPS, independent of this role.
