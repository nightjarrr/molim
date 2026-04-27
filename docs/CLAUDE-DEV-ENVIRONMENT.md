# Claude Code development environment

This document specifies the design of an isolated, ephemeral, hardened
container environment for running **Claude Code** against a GitHub-hosted
project repository. It covers the image, the network policy, the container
lifecycle, and the host-side and container-side scripts that bootstrap the
environment.

Companion to [`AGENTIC-SDLC.md`](AGENTIC-SDLC.md).

**Audience: human Project Owner only.** Read at setup time and when modifying the
environment. Not part of any agent's runtime context.

Throughout, `{owner}` and `{repo}` refer to the GitHub namespace and
repository name of the project.

---

## Host system

Linux only, tested on Ubuntu 24.04. Several decisions in this document —
POSIX shell launcher, Ghostty as terminal emulator, `docker run` as the
primary entry point — assume this target. Use on macOS or Windows is not
supported; adaptation to those hosts is left to the reader.

Prerequisites:

- Docker (or compatible OCI runtime). Engine sufficient; Desktop not
  required.
- Bash.
- Ghostty (or another GPU-capable terminal emulator).
- `libsecret-tools` (provides `secret-tool` for keyring access).
- `seahorse` (GUI for browsing and auditing the keyring).
- An active GNOME (or compatible Secret Service) login session, so that the keyring is unlocked.

Notably *not* required on the host: `git`, `gh`, `claude`, any language
runtime, any project-specific tooling. All of those live inside containers.

---

## Principles

**Ephemeral.** A container exists for one feature workflow and is destroyed
on exit. The only persistence channels are the Git repository on GitHub
(code, branches, artifacts) and GitHub Issues (state, labels, comments).
Anything not pushed before exit is lost — accepted trade-off for isolation
and reproducibility.

**Stateless agent, stateful world.** No agent state survives container
exit. Claude Code rebuilds context at session start by reading GitHub state
and repository artifacts.

**Defense in depth.** Three concentric trust boundaries:

1. **Container isolation** — host filesystem, network, and processes are
   inaccessible by default.
2. **Network policy** — outbound traffic restricted to a small allow-list,
   enforced inside the container at startup.
3. **Tool permissions** — Claude Code's agent, skill, tool restrictions
   enforce the SDLC's permission matrix.

The container is the single trust boundary between host and Claude Code.
Per-role separation is enforced inside the container by Claude Code's own
configuration.

**Push-only persistence.** The sole persistence channel out of the
container is `git push` to GitHub. No host filesystem bind mounts (beyond
read-only configuration injected by the launcher), no persistent volume for
`~/.claude`, no SSH agent forwarding. Credentials are injected as
environment variables at container start and discarded on exit.

**No plaintext secrets on host disk.** Authentication tokens (Claude Code
OAuth, GitHub Token) live in the host's Secret Service keyring, retrieved
on demand by the launcher. There is no `.env` file, no credentials file,
no token in shell history.

---

## Threat model

### Primary threat: host compromise from anything inside the development environment

The environment must prevent any code, tool, or AI agent running inside it
from affecting the host system. This is the principal driver of the
isolation design and the reason for several non-negotiable constraints:

- No `claude` install on the host (OAuth bootstrap uses a throwaway container).
- No filesystem mounts between host and container (no host home, no SSH
  keys, no project source bind, no `~/.claude` volume).
- No shared namespaces (no `--privileged`, no `--network=host`, no
  `--pid=host`, no `--ipc=host`).
- No Docker socket inside the container (mounting `/var/run/docker.sock`
  would be escape-equivalent).
- No host display or clipboard forwarding. The container has no `DISPLAY`,
  no X11 socket, no Wayland socket — in-container processes cannot
  programmatically read or write the host GUI clipboard. Normal
  copy/paste between Claude's TUI and the host (mouse selection, keyboard
  shortcuts in Ghostty) continues to work, mediated entirely by the
  terminal emulator.
- No outbound network paths back to the host. The container is on a
  Docker bridge network with a route to the host's bridge IP; the
  in-container firewall denies traffic to the bridge gateway and to
  RFC1918 ranges other than what is explicitly required.
- Non-root user inside the container.
- `--cap-drop=ALL` with deliberate add-back only of what is needed
  (`NET_ADMIN` for `init-firewall.sh`).
- `--security-opt no-new-privileges` to block setuid escalation.
- Read-only root filesystem, with `tmpfs` for the writable paths Claude
  needs.

**Limits of this isolation.** Container isolation reduces likelihood and
raises the skill bar; it does not reduce risk to zero. The host kernel
must be patched (Ubuntu's `unattended-upgrades` for the security pocket
suffices). The image is only as trustworthy as its build chain — pinned
digests, CI provenance, and base image discipline are part of the
mitigation. A determined attacker exploiting an unpatched container
escape CVE inside a compromised container is outside the design's
guarantees.

### Secondary threats

**Prompt injection.** Adversarial content (web pages, dependency READMEs,
issue bodies, fetched files) reaches Claude's context and attempts to
manipulate it. *Recognized.* Mitigated by ephemeral container isolation
(blast radius bounded to one session, one branch, one repository) and by
narrow GitHub Token scope (a manipulated Claude cannot push to other
repositories or modify account-level resources). Residual risk: hostile
content pushed to the feature branch under the Project Owner's identity until
caught at PR review.

**Malicious dependencies.** A package on a public registry runs hostile
code at install or test time. *Recognized.* Mitigated by Dependabot
scanning the repository, lockfile-pinned dependency installation in the
image build (no floating versions), and the SDLC's PR review on any
new-dependency addition. Theoretical residual risk accepted; image build
runs against locked manifests, so a compromised registry version that
bypasses Dependabot would still need to evade the next dependency-bump
PR review.

**Network exfiltration.** A compromised dependency or a manipulated Claude
attempts to send repository contents, secrets, or other data to an
attacker-controlled endpoint. *Recognized.* Primary driver of the network
policy: outbound traffic is restricted to a small allow-list (Anthropic
API, GitHub API, GitHub git endpoints, DNS) enforced by `init-firewall.sh`
at container start. An attacker who cannot reach `attacker-server.com`
cannot easily exfiltrate.

**Token theft.** An attacker inside the container reads
`CLAUDE_CODE_OAUTH_TOKEN` or `GH_TOKEN` from the process environment.
*Recognized.* Cannot be mitigated to zero — the container must hold the
tokens to function. Bounded by:

- Narrow scoping (GitHub Token: single repository; OAuth: one Anthropic
  account, revocable).
- Time-limited rotation (90-day GitHub Token rotation).
- Firewall-constrained exfiltration paths (a stolen token must still be
  sent somewhere reachable from the allow-list).
- No persistence on host disk (keyring, not files).
- Fast revocation paths (Anthropic console, GitHub UI; both
  ~30-second operations).

Accepted residual risk: an attacker in a single live session can use the
tokens at their granted scope for the session's lifetime.

**Quota and resource abuse.** A runaway Claude session — bug, prompt loop,
hostile instruction — burns through Anthropic quota, GitHub API rate
limits, or local CPU/memory/disk. *Recognized.* Mitigated by ephemeral
teardown (closing the terminal tab kills the container immediately) and
by container resource limits (`--memory`, `--cpus`) on `docker run` that
bound local resource impact regardless of in-container behavior. Small
residual exposure to Anthropic quota exhaustion (you notice when Claude
starts refusing requests; no real-time alerting available) and GitHub API
rate limits (5,000 requests/hour per token; failures appear as
backpressure) accepted.

---

## Container and session model

One container instance corresponds to one in-flight feature:

| Concept | Mapping |
| --- | --- |
| One GitHub Issue | One feature workflow |
| One feature workflow | One Claude Code session |
| One Claude Code session | One `claude` process |
| One `claude` process | One container |
| One container | One terminal tab (or `tmux` window) |

Claude Code subagents run inside the parent `claude` process and do not
require their own containers.

**Lifecycle.** Created when work on a feature begins
(`claude-dev.sh <issue-id>`), runs while work is active, destroyed when
work pauses or the feature merges. No long-running containers. Resuming a
paused feature creates a new container; Claude Code rebuilds context from
GitHub state.

**Concurrency.** Multiple features may be in flight in parallel, each in
its own container. Containers share no state with each other; mutual
visibility is via GitHub. The Project Owner switches features by switching
terminal tabs. Each `claude-dev.sh <issue-id>` invocation spins up a fresh
container; there is no "resume previous container" path.

**TUI requirements.** Claude Code is a TUI. The container provides a real
PTY (`docker run -it`), `TERM=xterm-256color`, and a UTF-8 locale
(`LANG=en_US.UTF-8`, `locales` package installed in the image).

**Survivability.** `claude` runs inside a `tmux` session inside the
container, so accidental terminal closes (lid close, X disconnect, SSH
drop) do not kill the session. Reattach with
`docker exec -it <container> tmux attach`. Survivability ends when the
container exits, by design.

---

## Authentication

Two secrets are required: a Claude Code OAuth token (for Anthropic API
access via the Pro/Max subscription) and a GitHub Token (a fine-grained
Personal Access Token for repository access). Both are stored in the host's
Secret Service keyring, retrieved on demand by the launcher, and injected
into the container as environment variables.

### Secret naming in keyring

| Secret | Service | Account |
| --- | --- | --- |
| Claude Code OAuth token | `claude-dev` | `claude-oauth` |
| GitHub Token | `claude-dev` | `github-token` |

Both share the `claude-dev` service namespace; the `account` attribute
distinguishes them.

### One-time bootstrap: Claude Code OAuth token

Acquired via a throwaway container that installs Claude Code from npm and
runs the OAuth setup flow. No host install of `claude` required.

```
docker run --rm -it node:20 \
  sh -c "npm install -g @anthropic-ai/claude-code && claude setup-token"
```

Procedure:

1. The container prints an authorization URL. Open it in the host browser.
2. Authorize. The browser displays a short-lived **authorization code**.
3. Paste the code back into the container's `setup-token` prompt.
4. Claude Code exchanges the code for the OAuth token and displays it.
5. Copy the OAuth token.
6. `Ctrl+C` the container (or let `setup-token` finish; the token is
   discarded with the container either way).
7. Store the token in the keyring on the host:

```
secret-tool store --label='Claude Code OAuth' \
  service claude-dev account claude-oauth
```

Paste the token at the prompt; press Enter. Verify in Seahorse: the entry
appears in the Login keyring with `service=claude-dev` and
`account=claude-oauth` attributes (Right-click → Properties → Details).

The trust chain is Docker Official `node:20` image, the public npm
registry, and the Anthropic-published `@anthropic-ai/claude-code` package.
No third-party Claude Code images are involved.

### One-time bootstrap: GitHub Token

Generated in the GitHub web UI and stored directly in the keyring; no
container involved.

1. In GitHub: Settings → Developer settings → Personal access tokens →
   Fine-grained tokens → Generate new token.
2. Scope and permissions per [GitHub Token scoping](#github-token-scoping)
   below.
3. Copy the token (shown once).
4. Store in the keyring:

```
secret-tool store --label='Claude Code GitHub Token' \
  service claude-dev account github-token
```

Paste the token; press Enter. Verify in Seahorse.

### Retrieval

The launcher retrieves both tokens at run time via `secret-tool lookup`:

```
CLAUDE_CODE_OAUTH_TOKEN=$(secret-tool lookup service claude-dev account claude-oauth)
GH_TOKEN=$(secret-tool lookup service claude-dev account github-token)
```

If either lookup returns empty, the launcher fails fast with a message
referencing the bootstrap procedure.

### Rotation

Both tokens are overwritten in place with the same `secret-tool store`
commands used during bootstrap (the same `service` + `account` attributes
identify and replace the existing entry). No file edits, no copy steps.

- **OAuth token rotation.** Re-run the bootstrap container, generate a new
  token, re-run the `secret-tool store` command for `claude-oauth`. Useful
  when changing Anthropic plans or after suspected compromise.
- **GitHub Token rotation.** Generate a new fine-grained token in GitHub,
  re-run the `secret-tool store` command for `github-token`. Recommended
  every 90 days.

### GitHub Token scoping

The GitHub Token's scope is the most consequential constraint on the
secondary-threat blast radius. A stolen or manipulated token can do
exactly what its scope permits, no more.

**Hard requirements** (inviolable; apply to every project):

- **Repository scope: single repository** (`{owner}/{repo}`). Not "all
  repositories", not "selected repositories" with more than one selected.
  A stolen token cannot reach any other repository.
- **No account-level permissions.** All entries under "Account
  permissions" remain at "No access". The token has no view of the
  GitHub account beyond the one repository.
- **No administration permissions.** The following repository
  permissions remain at "No access" regardless of project needs:
  Administration, Secrets, Variables, Environments, Deployments,
  Codespaces, Pages, Webhooks, Custom properties, Attestations. These
  modify the repository's configuration rather than performing work
  inside it; granting them would let a manipulated agent disable branch
  protection, exfiltrate secrets, rewrite CI to run attacker code, or
  similar.

**Baseline permissions** (required by the SDLC's current operations):

| Permission | Access | Why |
| --- | --- | --- |
| Metadata | Read | Implicit prerequisite for every other permission. GitHub auto-grants. |
| Contents | Read & write | Clone, fetch, push, branch creation and deletion. Phase 2 onwards. |
| Issues | Read & write | Phase 1 issue creation, label updates across all phases, phase comments. |
| Pull requests | Read & write | Phase 5 and release workflow PR creation, PR comments, status updates. |
| Workflows | Read & write | `chore` Issues that touch `.github/workflows/*`. Without this, those PRs cannot be pushed. |
| Actions | Read | Reading CI run status to confirm quality gates passed before proceeding to PR review. |

Workflows is the most consequential individual baseline permission — it
lets the token modify CI definitions. Accepted because the SDLC
explicitly governs `chore` work that touches workflows; the alternative
(manual edits outside the SDLC) defeats the design. The mitigation is
that workflow changes pass through PR review like any other change.

**Grey area** (project-specific; add only when a named operation
requires it):

| Permission | Consider when |
| --- | --- |
| Actions: write | The SDLC grows to include Claude triggering CI re-runs or cancelling stuck workflows. |
| Discussions: read/write | Project uses Discussions for design docs, RFCs, or decision records. |
| Packages: read | Project depends on private packages from GHCR or GitHub Packages. |
| Packages: write | Project publishes packages from CI and Claude drives the publish step. |
| Commit statuses: write | The SDLC adds a step where Claude posts custom commit statuses separate from CI. |
| Code scanning alerts: read | Quality gates include reading scanning results (CodeQL or similar). |
| Dependabot alerts: read | The SDLC includes a phase where Claude reviews and acts on Dependabot findings. |

The principle: start with the baseline, add a permission only when a
specific named SDLC operation requires it, document why in the project's
repository (not only in the token configuration). Drift toward "grant a
bit more just in case" is exactly what the no-administration policy
exists to prevent.

---

## Network policy

The container's outbound network is restricted to a small allow-list of
destinations required for Claude Code's normal operation. This is the
primary mitigation against the network exfiltration threat.

The policy is enforced by `init-firewall.sh`, run as the first step of
the entrypoint before any other network operation. It uses iptables
(requiring the `NET_ADMIN` capability granted by the launcher) to:

1. Set a default-deny outbound policy.
2. Resolve allow-listed hostnames to current IPs and install ACCEPT rules
   for them.
3. Install explicit DROP rules for the Docker bridge gateway and broader
   RFC1918 ranges, closing paths back to the host.
4. Allow DNS to the container's resolver.

The hostname-to-IP approach matches the Anthropic reference firewall.
Because GitHub and Anthropic endpoints are behind CDNs whose IPs may
rotate, very long sessions could see allow-listed hostnames resolve to
new IPs that are not in the rules. Mitigation: re-init the firewall by
restarting the container. The ephemeral session model makes this a
non-issue in practice.

### Allow-list

| Destination | Why |
| --- | --- |
| `api.anthropic.com` | Claude Code API calls |
| `statsig.anthropic.com` | Claude Code telemetry (current behavior; without this, Claude Code makes failed connection attempts at startup) |
| `github.com` | git clone, fetch, push over HTTPS |
| `api.github.com` | `gh` CLI for issues, PRs, labels, branch linkage |
| `*.githubusercontent.com` | Raw file fetches, release assets |
| DNS (UDP/TCP 53 to the container's resolver, typically `127.0.0.11`) | Hostname resolution for the above |

**Deliberately not on the list:**

- Package registries (PyPI, npm, etc.). Dependencies are baked into the
  image at build time using lockfile-frozen resolution; the running
  container has no need to reach registries.
- `ghcr.io`. The image is pulled by the launcher on the host, not from
  inside the container.

**Project-specific addition:** `objects.githubusercontent.com` (used by
Git LFS for large file downloads). Not in the default allow-list. Add it
in `init-firewall.sh` if the project uses Git LFS.

### Failure handling

`init-firewall.sh` failure is a hard error. If the firewall cannot be
installed — DNS resolution failure, iptables call failure, missing
capability — the entrypoint exits non-zero and the container terminates.
A container running without the firewall would have full default outbound
access, violating the threat model. There is no `|| true`, no fallback
to permissive mode, no warning-and-continue.

### Self-test

After firewall installation, the entrypoint runs two probes before
proceeding:

- **Negative probe.** A short-timeout request to a known-blocked
  destination (e.g., `curl --max-time 3 https://google.com`). Must fail.
  Confirms default-deny is in effect.
- **Positive probe.** A short-timeout request to a known-allowed
  destination (e.g., `curl --max-time 3 https://api.anthropic.com`).
  Must succeed. Confirms the allow-list is in effect.

If either probe gives the wrong result, the entrypoint exits non-zero and
the container terminates. This catches misconfigurations immediately
rather than after Claude Code starts misbehaving in non-obvious ways.

### Bootstrap container exception

The OAuth bootstrap container (`docker run ... node:20 ...` for
`claude setup-token`) does not run `init-firewall.sh` and is not subject
to this policy. It is a one-off operation outside the SDLC, uses a
different image, and needs to reach destinations (`claude.ai`, the npm
registry) that the runtime policy does not permit. Keeping it firewall-
exempt is intentional; the Project Owner runs it manually for a one-time
credential setup, not as part of the development workflow.

---

## Repository layout

The harness lives in the project repository, versioned with the code it
serves. A fresh clone of the repo is sufficient to bootstrap the
environment.

```
.devcontainer/
  Dockerfile                 # image definition
  devcontainer.json          # devcontainer metadata
  init-firewall.sh           # outbound network policy initialization
  entrypoint.sh              # in-container start: clone, checkout, exec claude
  image.digest               # pinned digest of the published image

.claude/                     # Claude Code project configuration

scripts/
  claude-dev.sh              # host-side launcher
  claude-dev.env             # per-project launcher configuration

.github/workflows/
  devenv.yml                 # builds and publishes the dev environment image
```

Modifications to the harness (`.devcontainer/`, `scripts/claude-dev.sh`,
`scripts/claude-dev.env`, `.github/workflows/devenv.yml`) follow the
project's regular SDLC as `chore` Issues.

---

## Image build and distribution

**Built by CI, hosted on GHCR.** GitHub Actions builds the image on changes
to harness paths and publishes to `ghcr.io/{owner}/{repo}-devenv`. GHCR is
free for public repositories with no storage or bandwidth caps. Local
`docker build` remains available as an offline / debugging fallback.

**Tags.**

| Tag | Updated when | Purpose |
| --- | --- | --- |
| `latest` | Push to `main` touching harness paths | Most recent stable build |
| `sha-{shortsha}` | Every build | Immutable, content-addressed |
| `weekly-{date}` | Scheduled weekly | Security-refresh rebuild |
| `pr-{n}` | PRs touching harness paths | Verification only |

**Pinned digest.** The launcher does not pull `:latest`. It pulls the
digest stored in `.devcontainer/image.digest`. Consequences: the
environment is reproducible from any commit (an old commit pulls the image
current at that commit), updates are explicit and go through a `chore`
Issue, and a bad `:latest` push cannot break ongoing work.

**Build context and dependency resolution.** The Dockerfile build context
is the repository root, not `.devcontainer/`. This lets the image bake in
language dependencies at build time using the project's manifests, keeping
container start fast. Dependency installation uses lockfile-frozen
resolution (`uv sync --frozen`, `npm ci`, equivalents) — no floating
versions, no fresh resolution at build time. This is both a performance
and a security property: the running container has no need to reach
package registries, and the firewall allow-list need not include them.

**Project runtime tooling.** Whatever the project's code needs to execute
end-to-end — system packages, external CLIs, additional language
toolchains — is installed into the image at build time. The principle:
the running container provides the full environment to write code, run
tests, and perform quality-gate verification. There is no "this only
runs in CI" carve-out; if the SDLC's quality gates depend on a tool,
that tool is in the image. Build-time installation also keeps the
runtime network policy small (no `apt-get`, no toolchain downloads at
container start).

---

## Launcher script (`claude-dev.sh`)

Host-side script. Single purpose: start the container. No knowledge of the
SDLC, no Issue-aware logic, no `gh` on the host.

```
claude-dev.sh <issue-id>
```

**Per-project configuration.** The launcher reads project identity from
`scripts/claude-dev.env` in the current repository checkout:

```
GH_OWNER=<github-namespace>
GH_REPO=<repository-name>
DEVENV_IMAGE=ghcr.io/<github-namespace>/<repository-name>-devenv
```

Colocated with the launcher under `scripts/` so both move together.

**Behavior.**

1. Source `scripts/claude-dev.env` from the repo root.
2. Read the pinned image digest from `.devcontainer/image.digest`.
3. Retrieve auth tokens from the Secret Service keyring:
   - `secret-tool lookup service claude-dev account claude-oauth`
   - `secret-tool lookup service claude-dev account github-token`
   Fail fast with a bootstrap-procedure pointer if either is empty.
4. `docker run --rm -it` with the pinned image, an interactive TTY,
   resource limits (`--memory`, `--cpus`), capability drop
   (`--cap-drop=ALL` plus `--cap-add=NET_ADMIN` for firewall init),
   `--security-opt no-new-privileges`, read-only root filesystem with
   tmpfs for required writable paths, and the env vars `GH_OWNER`,
   `GH_REPO`, `ISSUE_ID`, `CLAUDE_CODE_OAUTH_TOKEN`, `GH_TOKEN`. No bind
   mounts.
5. On exit, print the final `git status` and `git log origin/main..HEAD`
   from the container so the Project Owner sees what was pushed and what was
   not before the container is destroyed.

---

## Entrypoint script (`entrypoint.sh`)

Container-side script. The SDLC-aware bootstrap step, run as the
container's entrypoint. Receives `GH_OWNER`, `GH_REPO`, `ISSUE_ID`, `CLAUDE_CODE_OAUTH_TOKEN`, and `GH_TOKEN` via environment variables.

**Behavior.**

1. Run `init-firewall.sh` to install the outbound allow-list, then run
   the firewall self-test (negative + positive probes). Either failure
   aborts the container.
2. Configure git identity and HTTPS authentication via `GH_TOKEN`.
3. Clone `https://github.com/${GH_OWNER}/${GH_REPO}.git` into `/workspace`.
4. Look up the linked branch for the Issue:
   `gh issue develop ${ISSUE_ID} --list --repo ${GH_OWNER}/${GH_REPO}`.
   - **Empty result** — no branch yet. Remain on `main`. Branch creation
     happens during the SDLC's spec phase via `gh issue develop` invoked
     by AA.
   - **One linked branch** — check it out.
   - **Multiple linked branches** — refuse and exit. The Project Owner
     resolves the ambiguity in GitHub before retrying.
5. Print a brief summary: Issue title, current phase, branch state
   (fresh start vs resuming, commits ahead of `main` if resuming).
6. Start a `tmux` session and exec `claude` inside it.

**Branch lookup uses GitHub's first-class linkage**, not the branch
naming convention. The SDLC creates the link when the branch is created
(Phase 2); this script consumes it. The naming convention remains
documentation, per the SDLC. The entrypoint stays convention-agnostic:
changes to the naming convention require no changes here.

---

## Terminal emulator

**Ghostty** on the host. GPU-accelerated rendering (matters for Claude
Code's streaming output), Unicode and OSC 52 clipboard out of the box,
near-zero configuration.

Bump scrollback in `~/.config/ghostty/config`:

```
scrollback-limit = 100000000
```

Unit is bytes, ~100 MB.

---

## Explicit non-choices

Documented to prevent regression.

**No VS Code Dev Containers extension.** Its IPC sockets between host
VS Code and the container are a documented potential escape vector. The
workflow is terminal-first and does not need IDE integration.

**No persistent `~/.claude` volume.** Anthropic's reference devcontainer
mounts `~/.claude` to preserve OAuth tokens across rebuilds. Here,
credentials are injected via environment variable at container start; the
container exits with no Claude state on disk. Consistent with the
ephemeral model.

**No host home directory mount.** The container has no view of host
configuration files, SSH keys, or other personal state.

**No SSH agent forwarding.** GitHub access is via HTTPS using a
fine-grained GitHub Token scoped to the project repository, injected as
an environment variable.

**No `claude` install on the host.** Claude Code only runs inside
containers. The OAuth bootstrap uses a one-off `node:20` container with
`@anthropic-ai/claude-code` installed from npm, so no permanent Claude
Code presence on the host is required.

**No plaintext secrets on host disk.** Tokens live in the Secret Service
keyring (encrypted at rest, unlocked by the login session). No `.env`
files, no credentials files, no token in shell history. The launcher
retrieves on demand via `secret-tool`.

**No git worktrees.** Each container does its own `git clone`. Worktrees on
a shared host clone would reduce clone time but add complexity not
justified for small repositories and a single Project Owner.

**No save-on-exit.** The container exits with `--rm`; uncommitted work is
lost. The SDLC's "commit and push" discipline at every phase boundary
bounds this risk to one phase's work.

**No multi-container per-subagent isolation.** All Claude Code subagents
share a single container per feature. Per-role separation is enforced by
Claude Code's tool restrictions, not container boundaries. Multi-container
isolation per subagent would multiply operational complexity without
meaningful added isolation, since all subagents use the same OAuth token
and operate on the same working tree.

**No host-side `gh` or `git` dependency.** The launcher does not invoke
`gh` or `git` on the host. SDLC-aware operations (Issue lookup, branch
resolution, clone) happen inside the container, where the tools and
auth tokens already exist. The launcher's responsibility ends at "start
the container."

**No floating dependency versions.** Image build uses lockfile-frozen
resolution. Floating versions at build time would let a compromised
upstream release reach the image without review and would require the
firewall allow-list to include package registries at runtime.
