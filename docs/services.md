# Services Overview

## Caddy (Reverse Proxy)
- **Subdomain**: Gateway (handles all subdomains)
- **Ports**: 80 (HTTP→HTTPS redirect), 443 (HTTPS)
- **Purpose**: TLS termination, reverse proxy, static file server
- **Tech**: Caddy 2 with `caddy-dns/cloudflare` plugin
- **Config**: `/opt/tollgate/caddy/Caddyfile`

## strfry (Nostr Relay)
- **Subdomain**: `relay.<domain>`
- **Port**: 7777
- **Purpose**: General-purpose Nostr relay for event storage and relay
- **Tech**: C++ high-performance relay
- **Config**: `/opt/tollgate/strfry/strfry.conf`

## obelisk-relay (NIP-29 Group Chat)
- **Subdomain**: `chat.<domain>`
- **Port**: 8080
- **Purpose**: Relay-based group chat with NIP-29 support
- **Tech**: Rust (Tokio + Axum), prebuilt Docker image
- **Features**: Group management, roles, invite codes, admin UI

## blossom-server (Blob Storage)
- **Subdomain**: `blossom.<domain>`
- **Port**: 3001
- **Purpose**: Content-addressed blob storage for Nostr (BUD-01 to BUD-11)
- **Tech**: Deno 2 + TypeScript + Hono
- **Features**: Upload, download, mirror, media optimization, admin dashboard
- **Config**: `/opt/tollgate/blossom/config.yml`

## nsite-gateway (Static Site Gateway)
- **Subdomain**: `nsite.<domain>`
- **Port**: 3002
- **Purpose**: Serves Nostr-hosted static websites via HTTP
- **Tech**: Deno 2 + TypeScript + Hono
- **Features**: Hostname resolution, caching, homepage, status dashboard

## Tollgate Release Explorer
- **Subdomain**: `releases.<domain>`
- **Purpose**: Browse and download Tollgate firmware releases from Nostr
- **Tech**: React 18 static site
- **Source**: `https://github.com/OpenTollGate/tollgate-release-explorer-site`

## Hive CI Site
- **Subdomain**: `ci.<domain>`
- **Purpose**: Frontend for Hive CI decentralized CI/CD system
- **Tech**: Vue.js static site
- **Source**: `https://github.com/Origami74/hive-ci-site-mirror`

## Cashu Mint Orchestrator
- **Subdomain**: `*.mints.<domain>`
- **Ports**: 8085+ (one per mint)
- **Purpose**: Per-operator Cashu ecash mints
- **Tech**: CDK mintd Docker containers
- **Usage**: `./scripts/deploy-mint.sh <npub>`

## MPTCP Server
- **No subdomain** (TCP/UDP service)
- **Ports**: 65101 (Shadowsocks TCP), 65001 (Glorytun UDP)
- **Purpose**: Multi-path TCP aggregation for Tollgate routers
- **Tech**: shadowsocks-libev + glorytun
- **Config**: `/opt/tollgate/mptcp/server-config.txt`

## FIPS (Mesh Network)
- **No subdomain** (TUN interface)
- **Purpose**: Self-organizing encrypted mesh network using Nostr identities
- **Tech**: Rust, Noise Protocol, TUN/nftables
- **Config**: `/etc/fips/fips.yaml`

## nsyte CLI
- **No subdomain** (CLI tool)
- **Purpose**: Deploy and manage nsites from the VPS
- **Tech**: Deno 2 + TypeScript
- **Usage**: `nsyte deploy ./dist`
