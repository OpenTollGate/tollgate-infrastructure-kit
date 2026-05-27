#!/usr/bin/env python3

import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

GRASP_DATA_DIR = os.environ.get("GRASP_DATA_DIR", "/opt/tollgate/grasp/data")
GRASP_MIRROR_DIR = os.environ.get("GRASP_MIRROR_DIR", "/opt/tollgate/grasp-mirror")
OUTPUT = os.environ.get("GRASP_AUDIT_OUTPUT", "/tmp/grasp-audit.csv")


def run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()


def get_repo_sizes(base_dir):
    results = []
    repos_dir = os.path.join(base_dir, "git") if "grasp/data" in base_dir else os.path.join(base_dir, "repos")
    if not os.path.isdir(repos_dir):
        return results
    for entry in os.scandir(repos_dir):
        if not entry.is_dir():
            continue
        try:
            size_out = run(f"du -sb '{entry.path}' 2>/dev/null")
            size_bytes = int(size_out.split()[0])
        except (ValueError, subprocess.CalledProcessError):
            size_bytes = 0
        npub = ""
        if "npub" in entry.name:
            npub = entry.name.split("npub")[0].rstrip("/")
            if not npub:
                npub = "unknown"
        try:
            mtime = os.path.getmtime(os.path.join(entry.path, ".git", "HEAD")) if os.path.isdir(os.path.join(entry.path, ".git")) else entry.stat().st_mtime
        except OSError:
            mtime = entry.stat().st_mtime
        results.append({
            "path": entry.path,
            "name": entry.name,
            "npub": npub,
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "last_modified": mtime,
        })
    return results


def build_report(results):
    total = sum(r["size_bytes"] for r in results)
    total_mb = total / (1024 * 1024)

    npub_totals = {}
    for r in results:
        npub_totals.setdefault(r["npub"], {"count": 0, "bytes": 0})
        npub_totals[r["npub"]]["count"] += 1
        npub_totals[r["npub"]]["bytes"] += r["size_bytes"]

    sorted_npubs = sorted(npub_totals.items(), key=lambda x: x[1]["bytes"], reverse=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"GRASP Audit Report \u2014 {now}",
        f"Total repos: {len(results)} ({total_mb:.1f} MB)",
        "",
        "Top npubs by disk usage:",
    ]
    for npub, data in sorted_npubs[:20]:
        short = npub[:20]
        lines.append(f"  {short:20s}  {data['count']:3d} repos  {data['bytes']/(1024*1024):8.1f} MB")

    threshold_mb = int(os.environ.get("GRASP_AUDIT_DISK_THRESHOLD_MB", "500"))
    breaches = [r for r in results if r["size_mb"] > threshold_mb]
    lines.append("")
    lines.append(f"Disk threshold breaches (>{threshold_mb} MB): {len(breaches)}")
    if breaches:
        for b in breaches[:5]:
            lines.append(f"  {b['name'][:40]:40s}  {b['size_mb']:.1f} MB")

    return "\n".join(lines), sorted_npubs


def send_dm(report_text):
    hex_sk = os.environ.get("GRASP_AUDIT_HEX_SK", "")
    recipient_npub = os.environ.get("GRASP_AUDIT_RECIPIENT_NPUB", "")
    relays_str = os.environ.get("GRASP_AUDIT_RELAYS", "wss://relay.damus.io")
    relays = [r.strip() for r in relays_str.split(",") if r.strip()]

    if not hex_sk or not recipient_npub:
        print("GRASP_AUDIT_HEX_SK or GRASP_AUDIT_RECIPIENT_NPUB not set, skipping DM")
        return False

    try:
        from pynostr.event import Event
    except ImportError:
        print("pynostr not installed, skipping DM")
        return False

    try:
        from bech32 import bech32_decode, convertbits
        _, data = bech32_decode(recipient_npub)
        if data:
            recipient_hex = bytes(convertbits(data, 5, 8, False)).hex()
        else:
            print("Invalid recipient npub")
            return False
    except Exception as e:
        print(f"Failed to parse recipient npub: {e}")
        return False

    import hashlib, secp256k1, json as json_mod

    pubkey_bytes = bytes.fromhex(hex_sk)
    sk = secp256k1.PrivateKey(pubkey_bytes)

    event_obj = {
        "kind": 4,
        "content": report_text,
        "tags": [["p", recipient_hex]],
        "created_at": int(time.time()),
    }

    full_pubkey = sk.pubkey.serialize()
    event_obj["pubkey"] = full_pubkey[1:].hex()
    serialized = json_mod.dumps([0, event_obj["pubkey"], event_obj["created_at"], event_obj["kind"], event_obj["tags"], event_obj["content"]], separators=(',', ':'))
    event_id = hashlib.sha256(serialized.encode()).hexdigest()
    event_obj["id"] = event_id

    sig = sk.schnorr_sign(bytes.fromhex(event_id), None, raw=True)
    event_obj["sig"] = sig.hex() if isinstance(sig, bytes) else sig.serialize().hex()

    sent = False
    for relay_url in relays:
        try:
            import websocket
            ws = websocket.create_connection(relay_url, timeout=10, suppress_origin=True)
            ws.send(json_mod.dumps(["EVENT", event_obj]))
            result = ws.recv()
            ws.close()
            if "true" in result.lower() or "ok" in result.lower() or "\"error\"" not in result.lower():
                sent = True
                break
        except Exception as e:
            continue

    if sent:
        print(f"DM sent to {recipient_npub[:20]}... via {relay_url}")
        return True
    else:
        print(f"Failed to send DM to any relay")
        return False


def main():
    results = []
    results.extend(get_repo_sizes(GRASP_DATA_DIR))
    results.extend(get_repo_sizes(GRASP_MIRROR_DIR))

    results.sort(key=lambda x: x["size_bytes"], reverse=True)

    report_text, sorted_npubs = build_report(results)

    print(report_text)

    with open(OUTPUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "name", "npub", "size_bytes", "size_mb", "last_modified"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nFull report written to {OUTPUT}")

    if "--dm" in sys.argv:
        send_dm(report_text)


if __name__ == "__main__":
    main()
