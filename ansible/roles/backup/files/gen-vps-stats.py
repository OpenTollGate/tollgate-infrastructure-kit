#!/usr/bin/env python3
"""Generate machine status JSON with system resources + local service health.

Runs via systemd timer (every 10 seconds) and writes to the services dir.
Each VPS probes only its own local services (localhost, no CORS, instant).
"""
import json
import os
import socket
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

MACHINE_ID_FILE = "/etc/tollgate-machine-id"
STATS_DIR = "/srv/tollgate/services"
ENV_FILE = "/opt/tollgate/.env"


def load_env():
    env = {}
    if not os.path.exists(ENV_FILE):
        return env
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10, check=False)
        return r.stdout.strip()
    except Exception:
        return ""


def get_machine_id():
    if os.path.exists(MACHINE_ID_FILE):
        with open(MACHINE_ID_FILE) as f:
            return f.read().strip()
    return os.uname().nodename


def probe_http(url, timeout=3):
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "tollgate-stats/1.0")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return {"healthy": True, "status": resp.status, "ms": 0}
    except urllib.error.HTTPError as e:
        return {"healthy": e.code < 500, "status": e.code, "ms": 0}
    except Exception:
        return {"healthy": False, "status": 0, "ms": 0}


def probe_tcp(host, port, timeout=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        import time as _t
        start = _t.monotonic()
        s.connect((host, port))
        s.close()
        ms = int((_t.monotonic() - start) * 1000)
        return {"healthy": True, "ms": ms}
    except Exception:
        return {"healthy": False, "ms": 0}


def probe_docker_container(name):
    out = run(f"docker inspect --format '{{{{.State.Status}}}}' {name} 2>/dev/null")
    return {"healthy": out == "running", "status": out or "unknown"}


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


SERVICES_VPS = [
    {"name": "caddy",            "type": "http",  "url": "http://localhost:80"},
    {"name": "strfry",           "type": "tcp",   "host": "localhost", "port": 7777},
    {"name": "obelisk",          "type": "tcp",   "host": "localhost", "port": 8080},
    {"name": "blossom",          "type": "tcp",   "host": "localhost", "port": 3001},
    {"name": "nsite-gateway",    "type": "tcp",   "host": "localhost", "port": 3002},
    {"name": "releases",         "type": "http",  "url": "http://localhost/releases/"},
    {"name": "hive-ci",          "type": "http",  "url": "http://localhost/ci/"},
    {"name": "grasp",            "type": "tcp",   "host": "localhost", "port": 7334},
    {"name": "grasp-mirror",     "type": "http",  "url": "http://localhost:7335"},
    {"name": "test-mb-mint",     "type": "http",  "url": "http://localhost:8085/v1/info"},
    {"name": "test-kb-mint",     "type": "http",  "url": "http://localhost:8086/v1/info"},
    {"name": "test-gb-mint",     "type": "http",  "url": "http://localhost:8087/v1/info"},
    {"name": "test-min-mint",    "type": "http",  "url": "http://localhost:8088/v1/info"},
    {"name": "testnut-cdk",      "type": "http",  "url": "http://localhost:8091/v1/info"},
    {"name": "testnut-nutshell", "type": "http",  "url": "http://localhost:8092/v1/info"},
    {"name": "testnut-compat",   "type": "http",  "url": "http://localhost:8093/v1/info"},
    {"name": "routstr-mint",     "type": "http",  "url": "http://localhost:8089/v1/info"},
    {"name": "cashu-brrr",       "type": "http",  "url": "http://localhost:3000/api/health"},
    {"name": "mint-operator-proxy","type":"http", "url": "http://localhost:3000/api/health"},
    {"name": "routstr",          "type": "http",  "url": "http://localhost:8000/v1/models"},
    {"name": "ngit-relay",       "type": "tcp",   "host": "localhost", "port": 7778},
    {"name": "act-runner",       "type": "tcp",   "host": "localhost", "port": 8095},
    {"name": "relatr",           "type": "http",  "url": "http://localhost:3020"},
    {"name": "fips",             "type": "tcp",   "host": "localhost", "port": 8443},
    {"name": "micro-vpn",        "type": "http",  "url": "http://localhost:5010/api/v1/status"},
]

SERVICES_MAP = "auto"


def probe_services(services):
    results = {}
    for svc in services:
        name = svc["name"]
        if svc["type"] == "http":
            results[name] = probe_http(svc["url"])
        elif svc["type"] == "tcp":
            results[name] = probe_tcp(svc["host"], svc["port"])
        elif svc["type"] == "docker":
            results[name] = probe_docker_container(svc["container"])
    return results


PEER_FETCH = {
    "vps-1": {"peer_id": "vps-2", "peer_ip_env": "VPS2_IP"},
    "vps-2": {"peer_id": "vps-1", "peer_ip_env": "VPS_IP"},
}


def fetch_peer_status(machine_id):
    peer = PEER_FETCH.get(machine_id)
    if not peer:
        return
    env = load_env()
    peer_ip = env.get(peer["peer_ip_env"], os.environ.get(peer["peer_ip_env"], ""))
    if not peer_ip:
        return
    for path in [f"{peer['peer_id']}-status.json", "vps-stats.json"]:
        url = f"http://{peer_ip}/{path}"
        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("Host", "services.orangesync.tech")
            req.add_header("User-Agent", "tollgate-stats/1.0")
            resp = urllib.request.urlopen(req, timeout=5)
            if resp.status == 200:
                data = resp.read()
                try:
                    d = json.loads(data)
                    if d.get("machine_id") == peer["peer_id"] or path == "vps-stats.json":
                        peer_file = os.path.join(STATS_DIR, f"{peer['peer_id']}-status.json")
                        tmp = peer_file + ".tmp"
                        with open(tmp, "wb") as f:
                            f.write(data)
                        os.replace(tmp, peer_file)
                        return
                except (json.JSONDecodeError, ValueError):
                    pass
        except Exception:
            pass


def main():
    machine_id = get_machine_id()
    services = SERVICES_VPS if SERVICES_MAP == "auto" else SERVICES_MAP.get(machine_id, [])

    stats = {
        "machine_id": machine_id,
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
        "services": probe_services(services),
    }

    os.makedirs(STATS_DIR, exist_ok=True)
    output_file = os.path.join(STATS_DIR, f"{machine_id}-status.json")
    tmp = output_file + ".tmp"
    with open(tmp, "w") as f:
        json.dump(stats, f, indent=2)
    os.replace(tmp, output_file)

    fetch_peer_status(machine_id)

    old_file = os.path.join(STATS_DIR, "vps-stats.json")
    if os.path.exists(old_file) and not os.path.islink(old_file):
        os.remove(old_file)
    if not os.path.exists(old_file):
        os.symlink(f"{machine_id}-status.json", old_file)


if __name__ == "__main__":
    main()
