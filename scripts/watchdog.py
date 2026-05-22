#!/usr/bin/env python3
import json
import logging
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import urllib.request
import urllib.error

WATCHDOG_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = WATCHDOG_DIR / "scripts" / "watchdog.json"
ANSIBLE_DIR = WATCHDOG_DIR / "ansible"
ENV_FILE = WATCHDOG_DIR / ".env"
STATE_DIR = Path.home() / ".local" / "state" / "tollgate-watchdog"
LOG_DIR = Path.home() / ".local" / "log"
STATE_FILE = STATE_DIR / "state.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "watchdog.log", mode="a"),
    ],
)
log = logging.getLogger("tollgate-watchdog")


def load_env():
    env = {}
    if not ENV_FILE.exists():
        return env
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def load_state():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            log.warning("Corrupted state file — resetting")
    return {"last_redeploy": {}}


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def check_ssh(host, port, timeout):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True
    except (socket.timeout, socket.error, OSError):
        return False


def check_http(url, timeout):
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "tollgate-watchdog/1.0")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except Exception:
        return False


def run_ansible(playbook, env_vars):
    playbook_path = ANSIBLE_DIR / "playbooks" / playbook
    if not playbook_path.exists():
        log.error("Playbook not found: %s", playbook_path)
        return False

    cmd = [
        "ansible-playbook",
        str(playbook_path),
        "-i", str(ANSIBLE_DIR / "inventory" / "hosts.yml"),
    ]

    env = os.environ.copy()
    env.update(env_vars)

    log.info("Running ansible-playbook %s", playbook)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(ANSIBLE_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            log.info("Playbook %s succeeded", playbook)
            return True
        else:
            log.error("Playbook %s failed (rc=%d): %s", playbook, result.returncode, result.stderr[-500:])
            return False
    except subprocess.TimeoutExpired:
        log.error("Playbook %s timed out", playbook)
        return False


def render_url(template, env):
    url = template
    for key, val in env.items():
        url = url.replace("{{ " + key + " }}", val)
    return url


def check_cycle(config, env, context, state, ssh_host, ssh_port, ssh_timeout, http_timeout, cooldown, run_redeploy=True):
    check_interval = config.get("check_interval", 120)
    now = time.time()

    ssh_ok = check_ssh(ssh_host, ssh_port, ssh_timeout)
    if not ssh_ok:
        log.warning("SSH unreachable at %s:%d — skipping health checks", ssh_host, ssh_port)
        return {"ssh": False, "services": {}, "redeployed": []}

    results = {}
    down_services = []

    for svc in config.get("services", []):
        name = svc["name"]
        url = render_url(svc["url"], context)
        healthy = check_http(url, http_timeout)
        results[name] = {"healthy": healthy, "url": url}
        if not healthy:
            last_ts = state["last_redeploy"].get(name, 0)
            elapsed = now - last_ts
            if elapsed < cooldown:
                log.warning(
                    "Service %s DOWN (%s) — cooling down (%ds/%ds)",
                    name, url, int(elapsed), cooldown,
                )
                continue
            down_services.append(svc)
            log.warning("Service %s DOWN — %s", name, url)
        else:
            log.info("Service %s OK — %s", name, url)

    redeployed = []
    if down_services and run_redeploy:
        playbooks_to_run = []
        for svc in down_services:
            pb = svc["playbook"]
            if pb not in playbooks_to_run:
                playbooks_to_run.append(pb)

        ssh_user = env.get("VPS_USER", "debian")
        ssh_key = os.path.expanduser(env.get("SSH_PRIVATE_KEY_FILE", "~/.ssh/id_ed25519"))

        for pb in playbooks_to_run:
            affected = [s["name"] for s in down_services if s["playbook"] == pb]
            log.info("Redeploying %s for: %s", pb, ", ".join(affected))

            ansible_env = {
                "VPS_IP": ssh_host,
                "VPS_USER": ssh_user,
                "SSH_PRIVATE_KEY_FILE": ssh_key,
                "BASE_DOMAIN": context.get("base_domain", ""),
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            }
            for k, v in env.items():
                if k not in ansible_env:
                    ansible_env[k] = v

            success = run_ansible(pb, ansible_env)
            for svc in down_services:
                if svc["playbook"] == pb:
                    state["last_redeploy"][svc["name"]] = now
                    if success:
                        redeployed.append(svc["name"])
            save_state(state)

        for svc in down_services:
            url = render_url(svc["url"], context)
            healthy = check_http(url, http_timeout)
            status = "RECOVERED" if healthy else "STILL DOWN"
            log.info("Service %s: %s after redeploy", svc["name"], status)

    return {"ssh": True, "services": results, "redeployed": redeployed}


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    run_once = "--once" in sys.argv or "check" in sys.argv
    dry_run = "--dry-run" in sys.argv

    env = load_env()
    for k, v in env.items():
        os.environ.setdefault(k, v)

    base_domain = env.get("BASE_DOMAIN", "orangesync.tech")

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    check_interval = config.get("check_interval", 120)
    ssh_timeout = config.get("ssh_timeout", 10)
    http_timeout = config.get("http_timeout", 10)
    cooldown = config.get("cooldown", 600)

    ssh_cfg = config.get("ssh", {})
    ssh_host = env.get(ssh_cfg.get("host_env", "VPS_IP"), "")
    ssh_port = ssh_cfg.get("port", 22)

    context = {"base_domain": base_domain}
    state = load_state()

    log.info("Watchdog started — interval=%ds, cooldown=%ds, %d services", check_interval, cooldown, len(config.get("services", [])))

    if run_once or dry_run:
        result = check_cycle(config, env, context, state, ssh_host, ssh_port, ssh_timeout, http_timeout, cooldown, run_redeploy=not dry_run)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["ssh"] else 1)

    while True:
        check_cycle(config, env, context, state, ssh_host, ssh_port, ssh_timeout, http_timeout, cooldown, run_redeploy=True)
        time.sleep(check_interval)


if __name__ == "__main__":
    main()
