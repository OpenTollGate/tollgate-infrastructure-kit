#!/usr/bin/env python3
"""Audit GRASP server disk usage by npub and repo."""

import csv
import os
import subprocess
import sys
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


def main():
    results = []
    results.extend(get_repo_sizes(GRASP_DATA_DIR))
    results.extend(get_repo_sizes(GRASP_MIRROR_DIR))

    results.sort(key=lambda x: x["size_bytes"], reverse=True)

    total = sum(r["size_bytes"] for r in results)
    print(f"Total repos: {len(results)}")
    print(f"Total disk: {total / (1024*1024):.1f} MB")
    print()

    npub_totals = {}
    for r in results:
        npub_totals.setdefault(r["npub"], {"count": 0, "bytes": 0})
        npub_totals[r["npub"]]["count"] += 1
        npub_totals[r["npub"]]["bytes"] += r["size_bytes"]

    print("Top npubs by disk usage:")
    for npub, data in sorted(npub_totals.items(), key=lambda x: x[1]["bytes"], reverse=True)[:20]:
        print(f"  {npub[:20]:20s}  {data['count']:3d} repos  {data['bytes']/(1024*1024):8.1f} MB")

    with open(OUTPUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "name", "npub", "size_bytes", "size_mb", "last_modified"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nFull report written to {OUTPUT}")


if __name__ == "__main__":
    main()
