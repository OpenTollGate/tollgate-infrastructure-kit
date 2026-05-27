#!/usr/bin/env python3
"""Generate vps-stats.json with system resource usage.

Runs via systemd timer (every 10 seconds) and writes to the services dir.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

STATS_FILE = "/srv/tollgate/services/vps-stats.json"


def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10, check=False)
        return r.stdout.strip()
    except Exception:
        return ""


def get_cpu():
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        fields = line.split()
        user, nice, system, idle = int(fields[1]), int(fields[2]), int(fields[3]), int(fields[4])
        iowait = int(fields[5]) if len(fields) > 5 else 0
        total = user + nice + system + idle + iowait
        used = user + nice + system
        return round(used / total * 100, 1) if total > 0 else 0.0
    except Exception:
        return 0.0


def get_load():
    try:
        with open("/proc/loadavg") as f:
            parts = f.read().split()
        return [float(parts[0]), float(parts[1]), float(parts[2])]
    except Exception:
        return [0.0, 0.0, 0.0]


def get_memory():
    info = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(":")
                val = int(parts[1])
                info[key] = val
        total = info.get("MemTotal", 0) * 1024
        available = info.get("MemAvailable", 0) * 1024
        used = total - available
        swap_total = info.get("SwapTotal", 0) * 1024
        swap_free = info.get("SwapFree", 0) * 1024
        swap_used = swap_total - swap_free
        return {
            "total_bytes": total,
            "used_bytes": used,
            "available_bytes": available,
            "percent": round(used / total * 100, 1) if total > 0 else 0.0,
            "swap_total_bytes": swap_total,
            "swap_used_bytes": swap_used,
            "swap_percent": round(swap_used / swap_total * 100, 1) if swap_total > 0 else 0.0,
        }
    except Exception:
        return {}


def get_disk():
    out = run("df -B1 / | tail -1")
    if not out:
        return {}
    parts = out.split()
    if len(parts) < 6:
        return {}
    total = int(parts[1])
    used = int(parts[2])
    avail = int(parts[3])
    return {
        "total_bytes": total,
        "used_bytes": used,
        "available_bytes": avail,
        "percent": round(used / total * 100, 1) if total > 0 else 0.0,
    }


def get_uptime():
    try:
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        mins = int((seconds % 3600) // 60)
        return {"seconds": seconds, "human": f"{days}d {hours}h {mins}m"}
    except Exception:
        return {}


def get_top_processes(n=10):
    out = run(f"ps aux --sort=-%mem | head -{n + 1}")
    if not out:
        return []
    lines = out.strip().split("\n")
    procs = []
    for line in lines[1:]:
        parts = line.split(None, 10)
        if len(parts) < 11:
            continue
        procs.append({
            "user": parts[0],
            "pid": parts[1],
            "cpu_pct": float(parts[2]),
            "mem_pct": float(parts[3]),
            "vsz_mb": round(int(parts[4]) / 1024, 1),
            "rss_mb": round(int(parts[5]) / 1024, 1),
            "command": parts[10][:80],
        })
    return procs


def get_docker():
    out = run("docker stats --no-stream --format '{{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.MemPerc}}' 2>/dev/null")
    if not out:
        return []
    containers = []
    for line in out.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        containers.append({
            "name": parts[0],
            "cpu_pct": parts[1],
            "mem_usage": parts[2],
            "mem_pct": parts[3],
        })
    return containers


def get_cpu_cores():
    try:
        return os.cpu_count() or 1
    except Exception:
        return 1


def main():
    stats = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hostname": os.uname().nodename,
        "cpu_cores": get_cpu_cores(),
        "cpu_percent": get_cpu(),
        "load": get_load(),
        "memory": get_memory(),
        "disk": get_disk(),
        "uptime": get_uptime(),
        "top_processes": get_top_processes(12),
        "docker_containers": get_docker(),
    }

    tmp = STATS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(stats, f, indent=2)
    os.replace(tmp, STATS_FILE)


if __name__ == "__main__":
    main()
