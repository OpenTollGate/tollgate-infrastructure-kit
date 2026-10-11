.PHONY: deploy test teardown deploy-mint remove-mint lint check

deploy:
	@bash scripts/deploy.sh

test:
	@bash scripts/test.sh

teardown:
	@bash scripts/teardown.sh

deploy-mint:
	@bash scripts/deploy-mint.sh $(NPUB)

remove-mint:
	@bash scripts/remove-mint.sh $(MINT_ID)

lint:
	@echo "Linting Ansible playbooks..."
	ansible-lint ansible/playbooks/ ansible/roles/

check:
	@echo "Syntax check..."
	@ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-all.yml --syntax-check

# ---------------------------------------------------------------------------
# Dual-hosted Services PWA (kanban t_53d7a46d)
#
# ONE artifact, TWO hosts — see docs/CASHU-PWA-DUAL-HOSTING.md:
#   GitHub Pages  https://pwa.orangesync.tech      (public, free HTTPS)
#   this VPS      https://pwa-vps.orangesync.tech  (Caddy, role cashu_pwa)
# The VPS serves the identical tar.gz GitHub Pages serves (release asset
# pwa-dist-latest in felixfelix-bot/cashu.me), checksum-verified.
# ---------------------------------------------------------------------------
ENV_FILE ?= $(CURDIR)/.env
PWA_DOMAIN ?= orangesync.tech
PWA_HOST_PAGES ?= pwa.$(PWA_DOMAIN)
PWA_HOST_VPS ?= pwa-vps.$(PWA_DOMAIN)

.PHONY: pwa-dns pwa-deploy pwa-verify pwa-syntax

# Cloudflare records only (pwa CNAME -> GitHub Pages, pwa-vps A -> vps2).
# No VPS SSH required, so this leg is executable today.
pwa-dns:
	@test -f $(ENV_FILE) || { echo "ERROR: $(ENV_FILE) missing (needs BASE_DOMAIN, VPS2_IP, CLOUDFLARE_API_TOKEN)"; exit 1; }
	@set -a; . $(ENV_FILE); set +a; \
	ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook \
	  -i ansible/inventory/hosts.yml \
	  ansible/playbooks/53-cashu-pwa-dns.yml

# Install the published artifact on vps2 + render the pwa-vps Caddy vhost.
# GATED: requires SSH to the VPS (kanban t_8eb57e3a, TCP/22 unreachable).
pwa-deploy:
	@test -f $(ENV_FILE) || { echo "ERROR: $(ENV_FILE) missing"; exit 1; }
	@set -a; . $(ENV_FILE); set +a; \
	ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook \
	  -i ansible/inventory/hosts.yml \
	  ansible/playbooks/53-cashu-pwa.yml

pwa-syntax:
	@ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook \
	  -i ansible/inventory/hosts.yml \
	  ansible/playbooks/53-cashu-pwa.yml --syntax-check
	@ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook \
	  -i ansible/inventory/hosts.yml \
	  ansible/playbooks/53-cashu-pwa-dns.yml --syntax-check

# Read the live state back from both hosts.
pwa-verify:
	@echo "== canonical (GitHub Pages) =="
	@curl -fsS -o /dev/null -w "index     %{http_code} %{content_type}\n" https://$(PWA_HOST_PAGES)/ || echo "  unreachable"
	@curl -fsS -o /dev/null -w "manifest  %{http_code} %{content_type}\n" https://$(PWA_HOST_PAGES)/manifest.webmanifest || echo "  unreachable"
	@curl -fsS -o /dev/null -w "sw        %{http_code} %{content_type}\n" https://$(PWA_HOST_PAGES)/sw.js || echo "  unreachable"
	@echo "== self-host origin (vps2, gated on SSH) =="
	@curl -fsS -o /dev/null -w "index     %{http_code}\n" https://$(PWA_HOST_VPS)/ || echo "  vps leg NOT deployed (t_8eb57e3a)"
