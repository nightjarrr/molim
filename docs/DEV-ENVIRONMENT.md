# Claude Code development environment

This document specifies the design of an isolated, ephemeral, hardened
container environment for running **Claude Code** against a GitHub-hosted
project repository. It covers the image, the network policy, the container
lifecycle, and the host-side and container-side scripts that bootstrap the
environment.

Companion to [`AGENTIC-SDLC.md`](AGENTIC-SDLC.md).

**Audience: human operator only.** Read at setup time and when modifying the
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
visibility is via GitHub. The operator switches features by switching
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
2. Scope to the project repository only. Permissions: read/write Contents,
   Issues, Pull requests, Workflows; read Metadata.
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

**Build context.** The Dockerfile build context is the repository root,
not `.devcontainer/`. This lets the image bake in language dependencies at
build time using the project's manifests, keeping container start fast.

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
4. `docker run --rm -it` with the pinned image and an interactive TTY,
   passing `GH_OWNER`, `GH_REPO`, `ISSUE_ID`, `CLAUDE_CODE_OAUTH_TOKEN`,
   and `GH_TOKEN` as environment variables. No bind mounts.
5. On exit, print the final `git status` and `git log origin/main..HEAD`
   from the container so the operator sees what was pushed and what was
   not before the container is destroyed.

---

## Entrypoint script (`entrypoint.sh`)

Container-side script. The SDLC-aware bootstrap step, run as the
container's entrypoint. Receives `GH_OWNER`, `GH_REPO`, `ISSUE_ID`, `CLAUDE_CODE_OAUTH_TOKEN`, and `GH_TOKEN` via environment variables.

**Behavior.**

1. Configure git identity and HTTPS authentication via `GH_TOKEN`.
2. Clone `https://github.com/${GH_OWNER}/${GH_REPO}.git` into `/workspace`.
3. Look up the linked branch for the Issue:
   `gh issue develop ${ISSUE_ID} --list --repo ${GH_OWNER}/${GH_REPO}`.
   - **Empty result** — no branch yet. Remain on `main`. Branch creation
     happens during the SDLC's spec phase via `gh issue develop` invoked
     by AA.
   - **One linked branch** — check it out.
   - **Multiple linked branches** — refuse and exit. The Project Owner
     resolves the ambiguity in GitHub before retrying.
4. Print a brief summary: Issue title, current phase, branch state
   (fresh start vs resuming, commits ahead of `main` if resuming).
5. Start a `tmux` session and exec `claude` inside it.

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
justified for small repositories and a single operator.

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
