#!/usr/bin/env bash
# nosigner installer — NIP-46 remote signer (bunker) daemon.
#
# Usage (curl | bash):
#   curl -fsSL https://raw.githubusercontent.com/OpenTollGate/tollgate-infrastructure-kit/main/nosigner/install.sh | bash
#
# Options (env):
#   NOSIGNER_HOME     install dir (default: ~/.nosigner)
#   NOSIGNER_REPO_RAW raw base URL for the files (default: the repo main branch)
#   NOSIGNER_NO_SYSTEMD=1   skip the systemd --user unit (print how to run instead)
#
# It will: create a venv, install deps, install nosigner.py + nosigner_mcp.py,
# store your key at $NOSIGNER_HOME/nosigner.nsec (mode 0600), install a systemd
# --user unit, and print your bunker:// URL.
set -euo pipefail

NOSIGNER_HOME="${NOSIGNER_HOME:-$HOME/.nosigner}"
REPO_RAW="${NOSIGNER_REPO_RAW:-https://raw.githubusercontent.com/OpenTollGate/tollgate-infrastructure-kit/main/nosigner}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
PY="$(command -v python3 || true)"

say()  { printf '\033[1m%s\033[0m\n' "$*"; }
die()  { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

[ -n "$PY" ] || die "python3 not found"
"$PY" - <<'PY' || die "python3 >= 3.10 required"
import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY

say "→ Installing nosigner into $NOSIGNER_HOME"
mkdir -p "$NOSIGNER_HOME" "$NOSIGNER_HOME/venv"

# ── fetch a file: prefer a local copy next to this script, else download ──────
fetch() {
  local name="$1"
  if [ -n "$HERE" ] && [ -f "$HERE/$name" ]; then
    cp "$HERE/$name" "$NOSIGNER_HOME/$name"
  else
    curl -fsSL "$REPO_RAW/$name" -o "$NOSIGNER_HOME/$name" \
      || die "could not download $name from $REPO_RAW"
  fi
}

say "→ Downloading nosigner"
fetch nosigner.py
fetch nosigner_mcp.py
fetch requirements.txt
fetch nosigner.service

say "→ Creating venv + installing dependencies (coincurve, websockets, bech32)"
"$PY" -m venv "$NOSIGNER_HOME/venv"
"$NOSIGNER_HOME/venv/bin/pip" install --quiet --upgrade pip
"$NOSIGNER_HOME/venv/bin/pip" install --quiet -r "$NOSIGNER_HOME/requirements.txt"

# ── key setup (0600, never via argv) ─────────────────────────────────────────
KEY_FILE="$NOSIGNER_HOME/nosigner.nsec"
if [ -f "$KEY_FILE" ]; then
  say "→ Reusing existing key at $KEY_FILE"
else
  printf 'Paste your signer key (nsec1… or 64-hex). Input is hidden: '
  read -r -s SECRET; echo
  [ -n "$SECRET" ] || die "no key provided"
  if printf '%s' "$SECRET" | grep -q '^ncryptsec1'; then
    command -v nak >/dev/null 2>&1 || die "key is an ncryptsec but 'nak' is not installed (install nak to decrypt, or pass an nsec)"
    printf 'Password for the ncryptsec: '; read -r -s PW; echo
    SECRET="$(printf '%s' "$PW" | nak key decrypt "$SECRET" 2>/dev/null || true)"
    [ -n "$SECRET" ] || die "ncryptsec decryption failed"
  fi
  umask 077
  printf '%s' "$SECRET" > "$KEY_FILE"
  unset SECRET
fi
chmod 600 "$KEY_FILE"

# Derive the pubkey / bunker URL for display (nosigner's own crypto).
PUB="$("$NOSIGNER_HOME/venv/bin/python" - "$NOSIGNER_HOME" <<'PY' 2>/dev/null || true
import sys, importlib.util, pathlib
home = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("nosigner", home / "nosigner.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
sec = (home / "nosigner.nsec").read_text().strip()
pk = m.decode_nsec(sec) if sec.startswith("nsec1") else bytes.fromhex(sec)
print(m.privkey_to_pubkey(pk).hex())
PY
)"

# ── systemd --user unit ──────────────────────────────────────────────────────
if [ "${NOSIGNER_NO_SYSTEMD:-0}" != "1" ] && command -v systemctl >/dev/null 2>&1; then
  UNIT_DIR="$HOME/.config/systemd/user"; mkdir -p "$UNIT_DIR"
  sed "s|__NOSIGNER_HOME__|$NOSIGNER_HOME|g" "$NOSIGNER_HOME/nosigner.service" > "$UNIT_DIR/nosigner.service"
  systemctl --user daemon-reload || true
  systemctl --user enable --now nosigner.service || die "failed to start nosigner.service (see: journalctl --user -u nosigner)"
  sleep 2
  systemctl --user is-active nosigner.service >/dev/null && say "→ nosigner.service is running" \
    || die "nosigner.service did not start; check: journalctl --user -u nosigner -n 50"
else
  say "→ systemd skipped. Run manually:"
  echo "    $NOSIGNER_HOME/venv/bin/python $NOSIGNER_HOME/nosigner.py --sec-file $KEY_FILE --daemon"
fi

echo
say "✅ nosigner installed"
echo "   key:        $KEY_FILE (0600)"
[ -n "${PUB:-}" ] && echo "   pubkey:     $PUB"
[ -n "${PUB:-}" ] && echo "   bunker:     bunker://$PUB?relay=wss://relay.nsec.app&relay=wss://relay.primal.net&relay=wss://nostr.oxtr.dev"
echo "   logs:       journalctl --user -u nosigner -f"
echo
echo "Point clients/tools at the bunker:// URL above (NIP-46)."
