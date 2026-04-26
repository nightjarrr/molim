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

Notably *not* required on the host: `git`, `gh`, any language runtime, any
project-specific tooling. All of those live in the container image.

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
  claude-dev.env             # per-project launcher configuration
  claude-dev.sh              # host-side launcher

.github/workflows/
  devenv.yml                 # builds and publishes the dev environment image
```

Modifications to the harness (`.devcontainer/`, `scripts/claude-dev.sh`,
`.github/workflows/devenv.yml`) follow the project's regular SDLC as
`chore` Issues.

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
`claude-dev.env` in the current repository checkout:

```
GH_OWNER=<github-namespace>
GH_REPO=<repository-name>
DEVENV_IMAGE=ghcr.io/<github-namespace>/<repository-name>-devenv
```

**Behavior.**

1. Source `claude-dev.env` from the repo root.
2. Read the pinned image digest from `.devcontainer/image.digest`.
3. Read auth tokens (Claude Code OAuth, GitHub PAT) from the host.
4. `docker run --rm -it` with the pinned image and an interactive TTY,
   passing `GH_OWNER`, `GH_REPO`, `ISSUE_ID`, and the auth tokens as
   environment variables. No bind mounts beyond what credential injection
   requires.
5. On exit, print the final `git status` and `git log origin/main..HEAD`
   from the container so the operator sees what was pushed and what was
   not before the container is destroyed.

---

## Entrypoint script (`entrypoint.sh`)

Container-side entry point script. The SDLC-aware bootstrap step, run as
the container's entrypoint. Receives `GH_OWNER`, `GH_REPO`, `ISSUE_ID`, 
and auth tokens via environment variables.

**Behavior.**

1. Configure git identity and HTTPS authentication via the GitHub PAT.
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
scrollback-limit = 50000000
```

Unit is bytes, ~50 MB.

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
fine-grained Personal Access Token scoped to the project repository,
injected as an environment variable.

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
