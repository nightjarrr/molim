# Claude Dev Container — Current State / Handover

Purpose: dense implementation-state companion to `CLAUDE-DEV-ENVIRONMENT.md`. The master doc describes target state. This file describes what is currently implemented, what is known to work, what is intentionally deferred, and what remains to do.

Audience: AI agent or maintainer continuing implementation.

---

## Current status summary

* The project has moved from the original in-container firewall design to a host/sidecar-enforced proxy design.
* Claude dev container now runs successfully with:

  * `--network none`
  * `--cap-drop ALL`
  * `--security-opt no-new-privileges`
  * `--read-only`
  * explicit tmpfs writable mounts
  * proxy egress via mounted Unix socket + in-container `socat` bridge
* Envoy sidecar runs as a separate container, outside the Claude container.
* Envoy currently works as a dynamic forward proxy over Unix domain socket.
* Envoy currently allows all destinations during dogfooding. Domain allow-list exists conceptually/configurationally but is not enforced yet.
* Current priority changed from completing all hardening/publishing/allow-list work to dogfooding the container early.
* GHCR publishing, digest pinning, full Envoy allow-list, and other target-state items remain deferred.

---

## Repository / branch context

* Target design doc: `docs/CLAUDE-DEV-ENVIRONMENT.md`.
* Existing SDLC doc: `docs/AGENTIC-SDLC.md`.
* Host launcher: `scripts/claude-dev.sh`.
* Launcher config: `scripts/claude-dev.env`.
* Tmux seed config: `scripts/claude-dev.tmux.conf`.
* Claude container Dockerfile: `.devcontainer/claude-dev/Dockerfile`.
* Claude container entrypoint: `.devcontainer/claude-dev//entrypoint.sh`.
* Envoy config template: `.devcontainer/envoy/envoy.yaml.template`.

---

## Runtime architecture actually implemented

* Launcher starts one Envoy sidecar container per Claude session.
* Launcher then starts one Claude dev container per Claude session.
* Claude container has no Docker network: `--network none`.
* Envoy sidecar has normal egress network and performs DNS/upstream connections.
* Envoy listens on a Unix socket in a launcher-created runtime directory.
* Launcher bind-mounts the Envoy socket into Claude container as `/run/proxy.sock`.
* Claude entrypoint starts `socat`:
  * listens on `127.0.0.1:${CLAUDE_DEV_PROXY_PORT}`
  * forwards to `/run/proxy.sock`
* Claude entrypoint exports:
  * `HTTP_PROXY=http://127.0.0.1:${CLAUDE_DEV_PROXY_PORT}`
  * `HTTPS_PROXY=http://127.0.0.1:${CLAUDE_DEV_PROXY_PORT}`
  * lowercase equivalents
  * `NO_PROXY=localhost,127.0.0.1,::1`
* Proxy-aware tools work through Envoy.
* Tools bypassing proxy env vars have no network path.

---

## Launcher current behavior

* Host prerequisites currently checked:
  * `docker`
  * `secret-tool`
  * `tmux`
  * `openssl`
* `claude-dev.env` is sourced and required variables validated.
* Launcher seeds `~/.tmux.conf` from `scripts/claude-dev.tmux.conf` only if missing.
* Launcher sources `~/.tmux.conf` best-effort; failures are warnings, not fatal.
* Launcher creates a named tmux session and re-enters itself inside it.
* `TMUX_SESSION` must be exported before re-entry; Envoy logs tmux session depends on this.
* Launcher retrieves secrets from keyring:
  * `service=claude-dev account=claude-oauth`
  * `service=claude-dev account=github-token`
* Launcher creates Envoy per-run runtime directory under `${XDG_RUNTIME_DIR:-/tmp}/claude-dev/${RUN_ID}`.
* Launcher renders Envoy config from `.devcontainer/envoy/envoy.yaml.template`.
* Launcher starts Envoy sidecar detached with `--rm`.
* Launcher exposes Envoy admin on host loopback, currently `127.0.0.1:7001`.
* Launcher waits for Envoy socket before starting Claude container.
* Launcher starts optional detached tmux session running `docker logs -f ${ENVOY_CONTAINER}`.
* Launcher starts Claude container interactively with `docker run --rm -it`.
* Launcher cleanup stops Envoy container and removes runtime dir on exit.

---

## Claude container current `docker run` shape

Current important flags:

* `--network none`
* `--cap-drop ALL`
* `--security-opt no-new-privileges`
* `--read-only`
* tmpfs mounts:

  * `/tmp`
  * `/run`
  * `/var/tmp`
  * `/home/${CLAUDE_DEV_USER}`
  * `/workspace`
* `/home/${CLAUDE_DEV_USER}` and `/workspace` require `exec` because `uv`/project tooling may execute from there.
* `/run` should remain `noexec`.
* Envoy socket is bind-mounted to `${CLAUDE_DEV_PROXY_SOCKET_CONTAINER_PATH}`, currently `/run/proxy.sock`.
* Socket mount is expected to sit on top of tmpfs-mounted `/run`.

Current observed working tmpfs constraints during testing:

* `/home/node` tmpfs around 500M worked for current repo.
* `/workspace` tmpfs around 200M worked for current repo.
* `/tmp`, `/var/tmp`, `/run` small tmpfs mounts worked.
* Exact sizes should remain configurable; larger projects may require larger values.

---

## Envoy current behavior

* Envoy sidecar container starts and admin UI loads.
* Envoy listens on Unix domain socket.
* Unix socket verified directly with `curl --unix-socket` during smoke test.
* `socat` TCP-to-UDS bridge verified on host and in Claude container.
* Envoy dynamic forward proxy config works for:

  * plain HTTP proxy requests
  * HTTPS `CONNECT` tunneling
* Envoy access logs work after adding access log flush config.
* Access log line formatting fixed by ensuring real newline, not literal `\n`.
* Useful access log fields:

  * start time
  * method
  * `:authority`
  * path
  * response code
  * response flags
  * upstream host
  * duration
* Envoy currently still uses allow-all RBAC or equivalent temporary policy for dogfooding.
* Envoy allow-list should later be enforced via RBAC `action: ALLOW` and no catch-all deny filter.
* Virtual host `domains: ["*"]` should remain; security policy belongs in RBAC, not route matching.

---

## Envoy allow-list design decisions made

* Use Envoy RBAC `action: ALLOW` for default-deny semantics.
* No explicit wildcard deny rule needed.
* Optional explicit deny-list only makes sense later for hard-block overrides before broad allow patterns.
* Policy match basis: `:authority`.
* For HTTPS `CONNECT`, authority usually includes `host:port`, e.g. `api.github.com:443`.
* For plain HTTP, authority may be `host` or `host:port`.
* Allow-list entries should account for both forms where needed.
* Dynamic forward proxy cluster remains appropriate; allow-list restricts it before DNS/upstream connection.
* DNS for upstreams happens in Envoy sidecar, not Claude container.

---

## Current known network domains

Observed/expected during bootstrap and runtime:

* GitHub / git / gh:
  * `github.com:443`
  * `api.github.com:443`
* Python / uv:
  * `releases.astral.sh:443`
  * `pypi.org:443`
  * `files.pythonhosted.org:443`
* Claude runtime likely:
  * `api.anthropic.com:443`
  * additional Claude Code runtime/telemetry domains may appear during real use

Policy clarification:
* OS/toolchain dependencies should be baked into image.
* Project dependencies are only knowable after runtime repo clone and may require registry access.
* Runtime registry access is allowed when explicit, ecosystem-specific, and frozen/lockfile based.
* Runtime APT/OS package installation is not allowed.

---

## Entrypoint current behavior

* Uses `set -euo pipefail` during bootstrap.
* Prints section headers, warnings, and green check success lines.
* Validates required env vars.
* Configures ephemeral Bash prompt in `$HOME/.bashrc`.
* Prompt includes repo and optional issue, e.g. `[claude-dev molim #42] /workspace$`.
* Verifies `/workspace` is empty before clone.
* Runs warning/success diagnostics for:
  * network mode: loopback-only, no default route
  * capabilities: `CapEff=0000000000000000`
  * privileges: `NoNewPrivs=1`
  * read-only root
  * expected tmpfs mounts exist
  * expected tmpfs mounts writable by current user
  * writes outside approved mounts rejected
  * tmpfs ownership matches current UID/GID
  * `$HOME` and `/workspace` not `noexec`
  * `/run` is `noexec`
  * no unexpected writable non-tmpfs mounts
* Starts `socat` proxy bridge before any GitHub/git/uv network work.
* GitHub auth:
  * stores `GH_TOKEN` in temp variable
  * unsets `GH_TOKEN`
  * pipes token to `gh auth login --with-token --hostname github.com`
  * runs `gh auth setup-git`
  * runs `gh auth status`
* Configures git author using GitHub API user id/login.
* Clones repo into `/workspace`.
* Resolves linked GitHub issue branch via GraphQL `linkedBranches(first: 2)`.
* Initializes `~/.claude.json` from template using `CLAUDE_CODE_VERSION`.
* Runs project bootstrap currently via `uv sync --frozen`.
* Runs CMD (`claude` by default), then drops to interactive bash.
* On exit, prints git status and commits ahead of upstream/main.

---

## Tmux current behavior

* Launcher creates primary tmux session for Claude dev runtime.
* Launcher may create detached tmux session for Envoy logs:

  * name: `${TMUX_SESSION}-envoy-logs`
  * command: `docker logs -f ${ENVOY_CONTAINER}`
* `Ctrl-b d` detaches from tmux without killing underlying command.
* Tmux seed config is copied to `~/.tmux.conf` only if missing.
* Existing user `~/.tmux.conf` is never overwritten.
* Current tmux seed decisions:

  * mouse mode enabled
  * large scrollback
  * short `escape-time`
  * focus events
  * true color hints
  * clipboard/passthrough/title mutation disabled
  * slowed mouse-wheel scrolling via copy-mode bindings
  * `remain-on-exit failed` disabled due bad UX
* With mouse mode, terminal-native text selection may require Shift-drag.

---

## Hardening currently verified working

* `--network none` works.
* Proxy-aware tools still work via Envoy/socat.
* Proxy-bypass test works: unsetting proxy env vars causes `curl https://api.github.com` to fail with DNS/host resolution failure.
* `/sys/class/net` shows loopback-only in expected case.
* `--cap-drop ALL` works:

  * `CapEff: 0000000000000000`
* `--security-opt no-new-privileges` works:

  * `NoNewPrivs: 1`
* Read-only root works.
* Tmpfs mounts work after adding `exec` to `$HOME` and `/workspace`.
* `/run/proxy.sock` socket bind mount works on top of tmpfs `/run`.
* Docker-managed `/etc/hosts` appears as expected; not considered a hole.

---

## Current important config variables

Host/project launcher variables include at least:

* `GH_OWNER`
* `GH_REPO`
* `ENVOY_IMAGE`
* `ENVOY_ADMIN_HOST_PORT`
* `ENVOY_ADMIN_CONTAINER_PORT`
* `ENVOY_ADMIN_ADDRESS`
* `ENVOY_SOCKET_CONTAINER_PATH`
* `CLAUDE_DEV_IMAGE`
* `CLAUDE_DEV_USER`
* `CLAUDE_DEV_UID`
* `CLAUDE_DEV_GID`
* `CLAUDE_DEV_HOME_TMPFS_SIZE`
* `CLAUDE_DEV_WORKSPACE_TMPFS_SIZE`
* `CLAUDE_DEV_PROXY_SOCKET_CONTAINER_PATH`
* `CLAUDE_DEV_PROXY_PORT`

---

## Current implementation intentionally not complete

This list is a starting point for future implementation plan:
* Envoy allow-list not enforced yet; currently allow-all for dogfooding.
* GHCR image publishing not done / not prioritized immediately.
* Digest pinning not done / not prioritized immediately.
* Image provenance / scheduled rebuild workflow not complete.
* Image split into base and project not done.
* Base/project split of entrypoint not done.
* Project bootstrap still lives directly in entrypoint.
* Web Fetch / broad web research retrieval design deferred.
* Live Envoy allow-list management/control plane deferred.
* Credential-hiding via proxy/gateway deferred.
* Stronger isolation such as gVisor/VM deferred.
