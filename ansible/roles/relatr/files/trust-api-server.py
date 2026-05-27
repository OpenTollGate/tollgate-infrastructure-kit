#!/usr/bin/env python3

import json
import os
import shutil
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = os.environ.get("RELATR_DB_PATH", "/opt/tollgate/relatr/data/relatr.db")
DEFAULT_SOURCE = os.environ.get("RELATR_SOURCE_NPUB_HEX", "")
LISTEN_PORT = int(os.environ.get("TRUST_API_PORT", "3021"))
SNAPSHOT_DIR = "/tmp/relatr-snapshots"
SNAPSHOT_INTERVAL = int(os.environ.get("TRUST_API_SNAPSHOT_INTERVAL", "300"))
_last_snapshot = 0
_snapshot_path = os.path.join(SNAPSHOT_DIR, "relatr.db")


def get_snapshot():
    global _last_snapshot, _snapshot_path
    now = time.time()
    if now - _last_snapshot < SNAPSHOT_INTERVAL and os.path.exists(_snapshot_path):
        return _snapshot_path
    try:
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        shutil.copy2(DB_PATH, _snapshot_path)
        wal_path = DB_PATH + ".wal"
        if os.path.exists(wal_path):
            shutil.copy2(wal_path, _snapshot_path + ".wal")
        _last_snapshot = now
        return _snapshot_path
    except Exception as e:
        if os.path.exists(_snapshot_path):
            return _snapshot_path
        return None


class TrustHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/trust":
            self.handle_trust(parsed)
        elif parsed.path == "/health":
            self.handle_health()
        else:
            self.send_error(404)

    def handle_trust(self, parsed):
        params = parse_qs(parsed.query)
        pubkey = params.get("pubkey", [""])[0]
        if not pubkey:
            self.send_json({"error": "pubkey parameter required"}, 400)
            return
        try:
            score = self.get_trust_score(pubkey)
            self.send_json({"pubkey": pubkey, "score": score})
        except Exception as e:
            self.send_json({"pubkey": pubkey, "score": 0, "error": str(e)})

    def handle_health(self):
        snap = get_snapshot()
        if not snap:
            self.send_json({"status": "error", "error": "no snapshot"}, 503)
            return
        try:
            import duckdb
            conn = duckdb.connect(snap, read_only=True)
            count = conn.execute("SELECT COUNT(*) FROM nsd_root_distances").fetchone()[0]
            conn.close()
            self.send_json({"status": "ok", "pubkey_count": count})
        except Exception as e:
            self.send_json({"status": "error", "error": str(e)}, 503)

    def get_trust_score(self, pubkey):
        if pubkey.startswith("npub"):
            try:
                from bech32 import bech32_decode, convertbits
                _, data = bech32_decode(pubkey)
                if data:
                    hex_bytes = convertbits(data, 5, 8, False)
                    pubkey = bytes(hex_bytes).hex()
            except Exception:
                pass
        if not pubkey or len(pubkey) != 64:
            return 0.0
        snap = get_snapshot()
        if not snap:
            return 0.0
        try:
            import duckdb
            conn = duckdb.connect(snap, read_only=True)
            result = conn.execute(
                "SELECT distance FROM nsd_root_distances WHERE pubkey = ?",
                [pubkey]
            ).fetchone()
            conn.close()
            if result:
                distance = result[0]
                if distance == 0:
                    return 1.0
                elif distance == 1:
                    return 0.5
                elif distance == 2:
                    return 0.1
                else:
                    return 0.05
        except Exception:
            pass
        return 0.0

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", LISTEN_PORT), TrustHandler)
    print(f"Trust API listening on 127.0.0.1:{LISTEN_PORT}")
    print(f"Database: {DB_PATH}")
    print(f"Snapshot: {_snapshot_path}")
    print(f"Source pubkey: {DEFAULT_SOURCE[:16]}...")
    server.serve_forever()
