#!/usr/bin/env python3
"""Lightweight HTTP API that serves trust scores from Relatr's DuckDB database."""

import json
import os
import sys
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = os.environ.get("RELATR_DB_PATH", "/opt/tollgate/relatr/data/relatr.db")
DEFAULT_SOURCE = os.environ.get("RELATR_SOURCE_NPUB_HEX", "")
LISTEN_PORT = int(os.environ.get("TRUST_API_PORT", "3001"))


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
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.execute("SELECT COUNT(*) FROM metrics")
            count = cursor.fetchone()[0]
            conn.close()
            self.send_json({"status": "ok", "metrics_count": count})
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
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT trust_score FROM metrics WHERE target_pubkey = ? AND source_pubkey = ? ORDER BY computed_at DESC LIMIT 1",
                (pubkey, DEFAULT_SOURCE)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                return float(row["trust_score"])
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
    print(f"Source pubkey: {DEFAULT_SOURCE[:16]}...")
    server.serve_forever()
