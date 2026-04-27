# syntax=docker/dockerfile:1.7
# ======================================================================
# molim development environment image — initial skeleton (Phase 2, Step 4)
#
# This Dockerfile is organized into two logical sections:
#
#   1. BASE — the Claude Code development environment. Project-agnostic.
#      Eventually this section will be extracted into a separately-
#      published base image; for now it lives here for simplicity.
#
#   2. PROJECT — molim-specific tooling. Replaceable per project.
#
# Hardening (firewall enforcement, capability drops, read-only root) is
# added at Phase 3. Entrypoint logic (clone, branch checkout, exec
# claude) is added at Step 6.
# ======================================================================


# ======================================================================
# BASE — Claude Code development environment (project-agnostic)
#
# Pinned versions (update via chore Issue when bumping):
#   Base image:    node:24.15.0-bookworm-slim    # Active LTS, EOL Apr 2028
#   GitHub CLI:    2.91.0                        # Apr 22, 2026
#   Claude Code:   2.1.112                       # stable per npm registry
# ======================================================================

FROM node:24.15.0-bookworm-slim

# ----------------------------------------------------------------------
# Environment defaults that apply for both build and runtime.
# TZ is supplied by the launcher at run time (-e TZ=...) and read by
# libc and TZ-aware tools from the process environment; no ENV TZ here.
# ----------------------------------------------------------------------
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    TERM=xterm-256color \
    TZ=Etc/UTC

# ----------------------------------------------------------------------
# System packages required by the Claude Code dev environment
#
# General:
#   - locales: for the en_US.UTF-8 locale
#   - tzdata: zoneinfo files; required for run-time TZ env var resolution
#   - ca-certificates, curl: TLS + bootstrap downloads
#   - git: source control (used by the entrypoint and by Claude)
#   - tmux: in-container session survivability
#   - jq: JSON parsing (entrypoint and helpers)
#
# Claude operational tooling:
#   - bubblewrap: namespace-based sandbox used by Claude's `bash --sandbox`
#   - socat: socket relay used alongside bubblewrap for fine-grained
#     network access from sandboxed bash invocations
#   - ripgrep: Claude's preferred fast code search; significant speedup
#     vs grep on non-trivial repositories
#   - fd-find: Claude's preferred fast file finder; ergonomic counterpart
#     to ripgrep
#
# Firewall toolchain (used by init-firewall.sh at Phase 3):
#   - iptables: packet filtering
#   - ipset: efficient IP/CIDR set management
#   - iproute2: ip/route/link CLI; needed for bridge gateway detection
#   - dnsutils: dig/nslookup for hostname resolution
#   - aggregate: CIDR range compression for compact iptables rules
# ----------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        locales \
        tzdata \
        ca-certificates \
        curl \
        git \
        tmux \
        jq \
        bubblewrap \
        socat \
        ripgrep \
        fd-find \
        iptables \
        ipset \
        iproute2 \
        dnsutils \
        aggregate \
    && sed -i '/^#.* en_US.UTF-8 /s/^#//' /etc/locale.gen \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------------------------
# GitHub CLI (gh) — installed from the official .deb release
# ----------------------------------------------------------------------
RUN curl -fsSL "https://github.com/cli/cli/releases/download/v2.91.0/gh_2.91.0_linux_amd64.deb" \
        -o /tmp/gh.deb \
    && apt-get install -y /tmp/gh.deb \
    && rm /tmp/gh.deb \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------------------------
# Claude Code — official npm package, version-pinned
# ----------------------------------------------------------------------
RUN npm install -g @anthropic-ai/claude-code@2.1.112

# ----------------------------------------------------------------------
# Pre-create Claude Code's per-user state directory
# Claude Code expects ~/.claude to exist and be writable at first run;
# pre-creating it with correct ownership avoids first-run errors.
# Container is ephemeral so contents do not persist; this only ensures
# the directory exists with the right owner.
# ----------------------------------------------------------------------
RUN mkdir -p /home/node/.claude && chown -R node:node /home/node/.claude


# ======================================================================
# PROJECT — molim-specific tooling
#
# Pinned versions (update via chore Issue when bumping):
#   uv:            0.11.7                        # Apr 15, 2026
# ======================================================================

# ----------------------------------------------------------------------
# uv — copied from the official uv image, pinned to a specific version.
# Python itself is NOT installed at build time; uv installs the Python
# version specified by the project's .python-version / pyproject.toml
# at entrypoint time, after the repo is cloned.
# ----------------------------------------------------------------------
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/home/node/.cache/uv

# ----------------------------------------------------------------------
# molim runtime tooling — system binaries the project's code shells out to
# ----------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        imagemagick \
        ffmpeg \
        rawtherapee \
    && rm -rf /var/lib/apt/lists/*


# ======================================================================
# COMMON — user, working directory, default command
# ======================================================================

# Reuse the `node` user (UID/GID 1000) that ships with the base image.
USER node
WORKDIR /workspace

# Default command for Step 4 verification — interactive bash.
# Replaced by entrypoint.sh at Step 6.
CMD ["bash"]
