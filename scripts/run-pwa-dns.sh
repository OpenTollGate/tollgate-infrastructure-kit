#!/usr/bin/env bash
# Run the PWA DNS playbook (Cloudflare only, no VPS SSH needed).
# Secrets come from the primary infrastructure-kit .env; nothing is echoed.
set -euo pipefail
cd /home/c03rad0r/worktrees/t_53d7a46d-infra
set -a
# shellcheck disable=SC1091
. /home/c03rad0r/tollgate-infrastructure-kit/.env
set +a
export BASE_DOMAIN="${BASE_DOMAIN:-orangesync.tech}"
export VPS2_IP="${VPS2_IP:-23.182.128.51}"
export ANSIBLE_CONFIG=ansible/ansible.cfg
# ansible.cfg on main sets stdout_callback = yaml via community.general, which
# ansible-core 2.21 refuses to load; force the built-in callback.
export ANSIBLE_STDOUT_CALLBACK=default
exec ansible-playbook -i ansible/inventory/hosts.yml \
  ansible/playbooks/53-cashu-pwa-dns.yml "$@"
