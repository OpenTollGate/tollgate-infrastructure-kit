# Tollgate Infrastructure Kit

A single-command Ansible-based toolkit that deploys all Tollgate-related infrastructure services on a single VPS. Designed so anyone can run Tollgate infrastructure without depending on a small set of operators.

## Quick Start

```bash
# 1. Clone this repo
git clone https://github.com/OpenTollGate/tollgate-infrastructure-kit.git
cd tollgate-infrastructure-kit

# 2. Configure your environment
cp .env.example .env
# Edit .env with your VPS IP, domain, Cloudflare token, etc.

# 3. Deploy everything
make deploy
```

## Services Deployed

| Service | Subdomain | Description |
|---------|-----------|-------------|
| Caddy | (gateway) | Reverse proxy with automatic HTTPS |
| strfry | `relay.` | General-purpose Nostr relay |
| obelisk-relay | `chat.` | NIP-29 group chat relay |
| blossom-server | `blossom.` | Nostr blob storage (BUD-01 to BUD-11) |
| nsite-gateway | `nsite.` | Gateway for Nostr-hosted static sites |
| Release Explorer | `releases.` | Tollgate firmware release browser |
| Hive CI | `ci.` | Decentralized CI frontend |
| Cashu Mints | `*.mints.` | Per-operator Cashu ecash mints |
| MPTCP Server | (no subdomain) | Multi-path TCP aggregation |
| FIPS | (no subdomain) | Mesh network daemon |
| nsyte CLI | N/A | nsite deployment CLI tool |

## Prerequisites

- A VPS running Debian 13 (trixie) with a public IP
- SSH key access to the VPS
- A domain name managed by Cloudflare
- A Cloudflare API token with DNS edit permissions
- Ansible 2.14+ installed locally

## Configuration

All configuration is managed through the `.env` file. See `.env.example` for all available options.

Key variables:
- `VPS_IP` — Your VPS IP address
- `BASE_DOMAIN` — Your domain name
- `CLOUDFLARE_API_TOKEN` — Cloudflare API token
- `SHADOWSOCKS_PASSWORD` — Password for MPTCP server

## Available Commands

```bash
make deploy          # Deploy all services
make test            # Run integration and E2E tests
make teardown        # Remove all services
make deploy-mint     # Deploy a new Cashu mint (NPUB=<npub>)
make remove-mint     # Remove a Cashu mint (MINT_ID=<id>)
make lint            # Lint Ansible playbooks
make check           # Syntax check playbooks
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [Configuration Reference](docs/configuration.md)
- [Services Overview](docs/services.md)
- [Adding New Services](docs/adding-services.md)
- [Cloudflare Setup](docs/cloudflare-setup.md)
- [Troubleshooting](docs/troubleshooting.md)

## License

MIT
