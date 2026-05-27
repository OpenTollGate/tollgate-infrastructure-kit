#!/usr/bin/env python3
"""Clean GRASP repos from untrusted npubs using Relatr trust scores."""

import json
import os
import shutil
import subprocess
import sys

RELATR_URL = os.environ.get("RELATR_URL", "http://localhost:3000")
MIN_TRUST = float(os.environ.get("WOT_MIN_TRUST", "0.1"))
DRY_RUN = "--execute" not in sys.argv
GRASP_DATA_DIR = os.environ.get("GRASP_DATA_DIR", "/opt/tollgate/grasp/data")
GRASP_MIRROR_DIR = os.environ.get("GRASP_MIRROR_DIR", "/opt/tollgate/grasp-mirror")


def query_trust(npub_hex):
    try:
        result = subprocess.check_output(
            ["curl", "-s", "--max-time", "5", f"{RELATR_URL}/api/trust?pubkey={npub_hex}"],
            text=True
        )
        data = json.loads(result)
        return float(data.get("score", 0))
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError, KeyError):
        return 0.0


def find_repos(base_dir):
    repos = []
    repos_dir = os.path.join(base_dir, "git") if "grasp/data" in base_dir else os.path.join(base_dir, "repos")
    if not os.path.isdir(repos_dir):
        return repos
    for entry in os.scandir(repos_dir):
        if entry.is_dir():
            repos.append(entry.path)
    return repos


def extract_npub(path):
    name = os.path.basename(path)
    parts = name.split("/")
    for p in parts:
        if p.startswith("npub"):
            return p
    return ""


def main():
    all_repos = []
    all_repos.extend(find_repos(GRASP_DATA_DIR))
    all_repos.extend(find_repos(GRASP_MIRROR_DIR))

    print(f"Scanning {len(all_repos)} repos...")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'EXECUTE'}")
    print(f"Min trust: {MIN_TRUST}")
    print()

    npubs_seen = {}
    for repo_path in all_repos:
        npub = extract_npub(repo_path)
        if npub and npub not in npubs_seen:
            npubs_seen[npub] = query_trust(npub)

    flagged = []
    total_reclaimable = 0

    for repo_path in all_repos:
        npub = extract_npub(repo_path)
        score = npubs_seen.get(npub, 0.0)
        try:
            size = int(subprocess.check_output(["du", "-sb", repo_path], text=True).split()[0])
        except (subprocess.CalledProcessError, ValueError):
            size = 0

        if score < MIN_TRUST:
            flagged.append({"path": repo_path, "npub": npub, "score": score, "size": size})
            total_reclaimable += size

    print(f"Trust scores computed for {len(npubs_seen)} unique npubs")
    print(f"Flagged {len(flagged)} repos from untrusted npubs")
    print(f"Reclaimable: {total_reclaimable / (1024*1024):.1f} MB")
    print()

    for f in flagged:
        action = "WOULD REMOVE" if DRY_RUN else "REMOVING"
        print(f"  [{action}] score={f['score']:.3f} size={f['size']/(1024*1024):.1f}MB {f['path']}")

        if not DRY_RUN:
            shutil.rmtree(f["path"], ignore_errors=True)

    if DRY_RUN and flagged:
        print()
        print("Run with --execute to actually remove flagged repos.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
