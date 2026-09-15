# nosigner — NIP-46 remote signer (bunker) daemon

A small, self-hosted **NIP-46 remote signer** you run on your own computer. It
replaces flaky phone/web bunkers (Amber, `nak bunker`) for unattended signing:
ngit pushes, Nostr event publishing, CI, retractions, etc.

- **NIP-46** remote signer over Nostr relays (kind `24133`)
- **NIP-44 v2** encryption of the request/response channel
- SQLite **authorized-keys** store (approve a client once; no per-request prompt)
- `--daemon` (systemd `--user`) or `--one-shot`
- Package also ships `nosigner_mcp.py`, an **MCP server** exposing
  `sign_event` / `get_pubkey` / `bunker_status` / `bunker_url`

> Why not Amber? Amber is Android-only and a NIP-46 bunker signs only as its own
> pubkey; stale mobile sessions produce `already connected` hangs. nosigner runs
> headless on the machine that needs to sign.

## Install (one line)

```bash
curl -fsSL https://raw.githubusercontent.com/OpenTollGate/tollgate-infrastructure-kit/main/nosigner/install.sh | bash
```

The installer:

1. creates `~/.nosigner/venv` and installs `coincurve`, `websockets`, `bech32`;
2. downloads `nosigner.py` + `nosigner_mcp.py`;
3. prompts for your key (**hidden input**) and stores it at
   `~/.nosigner/nosigner.nsec` with mode `0600`. It accepts an `nsec1…` /
   64-hex key, or an `ncryptsec1…` (NIP-49) which it decrypts with `nak key
   decrypt`;
4. installs and starts a **systemd `--user`** unit (`nosigner.service`);
5. prints your `bunker://` URL and pubkey.

Environment overrides: `NOSIGNER_HOME` (install dir), `NOSIGNER_REPO_RAW`
(file source), `NOSIGNER_NO_SYSTEMD=1` (skip the unit).

## Manual run (no systemd)

```bash
~/.nosigner/venv/bin/python ~/.nosigner/nosigner.py \
  --sec-file ~/.nosigner/nosigner.nsec --daemon \
  --relay wss://relay.nsec.app --relay wss://relay.primal.net --relay wss://nostr.oxtr.dev
```

`--sec-file` is preferred over `--sec` so the key never appears in `ps`/argv.

## Point tools at it

Use the printed `bunker://<pubkey>?relay=…&relay=…` URL with any NIP-46 client:

```bash
ngit account login --bunker-url 'bunker://<pubkey>?relay=wss://relay.nsec.app'
nak event --sec 'bunker://<pubkey>?relay=wss://relay.nsec.app&secret=<secret>' ...
```

New clients are **denied until authorized**. Authorize by completing the initial
`connect` (a `secret` in the bunker URL, or an approved client key). Authorized
keys live in `~/.hermes/state/bunker/state.db` (SQLite).

## MCP server

`nosigner_mcp.py` wraps the daemon for agent use (tools: `sign_event`,
`get_pubkey`, `bunker_status`, `bunker_url`). Register it in your MCP config:

```json
{ "mcpServers": { "nosigner": { "command": "~/.nosigner/venv/bin/python",
  "args": ["~/.nosigner/nosigner_mcp.py"] } } }
```

## Security notes

- The signer key is a **bearer secret on this machine**. It is stored `0600`;
  keep the host hardened and the account private.
- For stronger at-rest protection, keep the key as a NIP-49 `ncryptsec` and
  supply the password at start (the installer supports decrypt-on-install; a
  fully non-interactive ncryptsec-at-rest mode is a planned follow-up).
- The systemd unit runs with `NoNewPrivileges`, `PrivateTmp`,
  `ProtectSystem=strict`, `ProtectHome=read-only`.
- Never paste a main-identity nsec into a shell history; the installer uses
  hidden input and writes the key directly to a `0600` file.

## Troubleshooting

- `journalctl --user -u nosigner -f` — logs (`~/.hermes/logs/nosigner/nosigner.log`).
- `already connected` from a client → that's the client's stale session; delete
  the client key/state (nosigner keeps its own authorized-keys DB).
- Restart: `systemctl --user restart nosigner`.
- Remove: `systemctl --user disable --now nosigner && rm -rf ~/.nosigner`.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install -r nosigner/requirements.txt
.venv/bin/python -m pytest nosigner/tests -q
```
