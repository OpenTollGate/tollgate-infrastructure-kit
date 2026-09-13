# ACT Runner on DQ05

DQ05 runs the fleet's own `act_runner` so the org can keep running CI while
GitHub Actions is unavailable for `OpenTollGate` (org suspended).

- Playbook: `ansible/playbooks/27-act-runner.yml` (`hosts: ci_runners`)
- Role: `ansible/roles/act_runner/`
- Host values: `ansible/inventory/host_vars/dq05.yml`
- Group floor: `ansible/inventory/group_vars/ci_runners.yml`

Unlike vps1/vps2 this host is **not** a dedicated runner: it is a 4 CPU /
10 GiB machine carrying production co-tenants, and it forwards fleet
inference over a tunnel. Everything below exists so that running CI on DQ05
cannot starve them.

## Co-tenants the caps are sized against

| Co-tenant | Port | Note |
| --- | --- | --- |
| `llama-server` | 8082 | local inference |
| `fips-exit-*` stack | — | fleet exit nodes |
| `ngit-ci-deploy-coordinator-1` | — | the *other* CI mechanism |
| `ngit-ci-deploy-dind-1` | 2375-2376 | dind for ngit CI |
| strfry relay | 7780 | relay the runner also publishes to |

## Resource caps

Measured at deploy time: 4 CPUs, 10 GiB RAM (~5 GiB available), 468 GB disk
(~139 GB free), 38 GiB swap with ~7.8 GiB already in use, load
1.95 / 1.24 / 1.53.

| Knob | Value | Why |
| --- | --- | --- |
| `act_runner_job_concurrency` | `1` | one pushed commit can never start a second parallel job |
| `act_runner_container_options` | `--memory=2g --memory-swap=2g --cpus=1.5 --pids-limit=512` | 2 GiB ≈ 40% of available RAM; `--memory-swap == --memory` stops a job growing into the ~7.8 GiB of already-consumed swap; 1.5 of 4 CPUs leaves 2.5 for llama-server / fips-exit; `--pids-limit` bounds fork bombs |
| `act_runner_systemd_cpu_quota` | `150%` | daemon only (watcher `git` + the `act` process) |
| `act_runner_systemd_memory_max` | `768M` | daemon only |

Worst case on DQ05: 1.5 CPU + 2 GiB (job container) **plus** 1.5 CPU +
768 MiB (daemon) = at most 3 of 4 CPUs and ~2.8 GiB of the ~5 GiB available.

The systemd caps do **not** bound job containers — `act` starts those in
their own cgroups. That is what `--container-options` is for; both are set.

## Capability envelope — what this lane can and cannot run

`act` executes a workflow inside a single job container using the host
docker daemon. It gives that container **no nested docker daemon**.

Fits:

- Go build / test / vet / lint (`go-test`, `main-test`, `contract-lint`,
  `build-purity`, `deps-and-imports` lanes of `tollgate-module-basic-go`)
- pure shell / script lanes

Does NOT fit:

- docker/SDK lanes (multi-arch OpenWrt SDK packaging, image builds) — no
  nested docker daemon
- anything needing a `container:` or `services:` block **with options**
- job-level `uses:` (only step-level)
- 30-minute default job timeout is the ceiling; there is no `GITHUB_TOKEN`

Also: ngit CI executes `.ngit/act/workflows/` only, so a workflow that lives
anywhere else is invisible to this runner.

## Host differences from the VPS runners

1. **Account.** DQ05 has no `debian` user. `act_runner_user` /
   `act_runner_group` are `c03rad0r`; both the role and the systemd unit are
   parameterized, nothing is hardcoded to `debian`.
2. **Repo allowlist.** The shared allowlist points at the
   `http://localhost:7334` GRASP mirror on vps1. From DQ05 port 7334 is not
   listening (`curl` → `000`), so the host overrides `act_runner_repos` with
   GitHub URLs (`https://github.com/OpenTollGate/tollgate-module-basic-go.git`,
   reachable: HTTP 200, `git ls-remote` HEAD `60530c67`).
3. **Relays.** `orangesync.tech` does not resolve from DQ05
   (`ngit1`/`relay1`/`runner`/`git.*` all → `000`), so the shared
   `wss://ngit.*` / `wss://relay.*` list would publish events into the void.
   DQ05 publishes to its own strfry at `ws://127.0.0.1:7780`.
4. **No Caddy.** DQ05 has no public subdomain, so the role's final
   `https://{{ act_runner_domain }}/api/health` check would fail the play
   *after* a successful deploy. `act_runner_verify_caddy: false` gates it;
   reachability is verified on `http://localhost:8095/api/health` instead,
   which always runs.

## `act` version

DQ05 runs `act` **0.2.89** at `/usr/local/bin/act`; the VPS runners pin
0.2.77. The role's install task is `creates:`-guarded, so it never replaces
an existing binary — the node would otherwise silently drift from the
version the role names.

Handled explicitly rather than silently:

- `act_runner_version` is a real role variable (it used to be hardcoded in
  the install task).
- `ansible/inventory/host_vars/dq05.yml` declares `0.2.89`, i.e. what is
  actually deployed, so the declaration matches reality.
- The role reads `act --version` and prints an **ACT VERSION DRIFT** warning
  when the installed binary does not contain the declared version.
- Both flags the runner passes (`--concurrent-jobs`, `--container-options`)
  exist in 0.2.89 — verified with `act push --help` on DQ05.

## Verifying a deploy

```bash
cd ansible
ansible-playbook -i inventory/hosts.yml playbooks/27-act-runner.yml --syntax-check
ansible-playbook -i inventory/hosts.yml playbooks/27-act-runner.yml --limit dq05 --check --diff
ansible-playbook -i inventory/hosts.yml playbooks/27-act-runner.yml --limit dq05
ssh c03rad0r@<dq05> 'curl -s http://localhost:8095/api/health | python3 -m json.tool'
bash ../tests/integration/test_act_runner.sh c03rad0r@<dq05>   # ACT_RUNNER_CADDY=0
```

`tests/integration/test_act_runner.sh` takes the target as `$1` and skips
the Caddy checks when `ACT_RUNNER_CADDY=0`.
