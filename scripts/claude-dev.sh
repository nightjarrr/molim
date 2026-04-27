#!/bin/bash
# ======================================================================
# claude-dev.sh — Claude Code dev environment launcher
#
# Single purpose: start the container.
# Reads project identity from claude-dev.env, retrieves auth tokens from
# the host Secret Service keyring, detects host timezone, and runs the
# dev environment image with an interactive TTY.
#
# Usage:
#   claude-dev.sh                            # no issue; default command
#   claude-dev.sh <issue-id>                 # specific Issue; default command
#   claude-dev.sh -- <cmd> [args...]         # no issue; override command
#   claude-dev.sh <issue-id> -- <cmd> [args] # specific Issue; override command
#
# The default command is whatever the image's CMD specifies (currently
# bash; will become tmux + claude in Step 7). The override is intended
# for troubleshooting (e.g., running `uv run pytest` against a fresh
# clone without entering an interactive session).
#
# [TODO] Hardening flags, GHCR pull, digest pinning, entrypoint logic, and
# pre-exit reporting are added in later steps.
# ======================================================================

set -euo pipefail

# ----------------------------------------------------------------------
# Locate this script's directory (so we can find claude-dev.env beside it)
# ----------------------------------------------------------------------
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="${SCRIPT_DIR}/claude-dev.env"

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
die() {
    echo "Error: $*" >&2
    exit 1
}

usage() {
    cat >&2 <<EOF
Usage: claude-dev.sh [<issue-id>] [-- <cmd> [args...]]

  <issue-id>     Optional. Positive integer GitHub Issue number to work on.
                 If omitted, the container starts without a specific Issue
                 context (suitable for the "New Issue" skill or general work).

  -- <cmd>...    Optional. Override the image's default command. Useful for
                 one-off troubleshooting against a freshly bootstrapped
                 workspace.

Examples:
  claude-dev.sh                              # session with no Issue
  claude-dev.sh 42                           # session for Issue #42
  claude-dev.sh -- ls -la /workspace         # one-off ls, no Issue
  claude-dev.sh 42 -- uv run pytest -q       # one-off pytest for Issue #42
EOF
}

# ----------------------------------------------------------------------
# Argument parsing
#
# Accepts:
#   (no args)
#   <issue-id>
#   -- <cmd> [args...]
#   <issue-id> -- <cmd> [args...]
# ----------------------------------------------------------------------
ISSUE_ID=""
CMD_OVERRIDE=()
POSITIONAL=()
SEPARATOR_FOUND=0

# Walk the args; everything before -- is positional, everything after is
# the command override.
for arg in "$@"; do
    if [[ "$SEPARATOR_FOUND" -eq 0 ]]; then
        if [[ "$arg" == "--" ]]; then
            SEPARATOR_FOUND=1
        else
            POSITIONAL+=("$arg")
        fi
    else
        CMD_OVERRIDE+=("$arg")
    fi
done

# If the separator was given, a command must follow it.
if [[ "$SEPARATOR_FOUND" -eq 1 ]] && [[ ${#CMD_OVERRIDE[@]} -eq 0 ]]; then
    usage
    die "'--' was given but no command followed it"
fi

# Positional args (before --) carry the optional issue ID. Zero or one,
# nothing else.
if [[ ${#POSITIONAL[@]} -gt 1 ]]; then
    usage
    die "expected at most one positional argument before '--', got ${#POSITIONAL[@]}"
fi

if [[ ${#POSITIONAL[@]} -eq 1 ]]; then
    if [[ ! "${POSITIONAL[0]}" =~ ^[1-9][0-9]*$ ]]; then
        usage
        die "issue ID must be a positive integer, got '${POSITIONAL[0]}'"
    fi
    ISSUE_ID="${POSITIONAL[0]}"
fi

# ----------------------------------------------------------------------
# Prerequisite tool checks
# ----------------------------------------------------------------------
require_tool() {
    local tool="$1"
    local hint="$2"
    if ! command -v "$tool" >/dev/null 2>&1; then
        die "required tool '$tool' not found in PATH. ${hint}"
    fi
}

require_tool docker      "Install Docker Engine (https://docs.docker.com/engine/install/)."
require_tool secret-tool "Install libsecret-tools (apt install libsecret-tools)."

# ----------------------------------------------------------------------
# Load and validate claude-dev.env
# ----------------------------------------------------------------------
if [[ ! -f "$ENV_FILE" ]]; then
    die "claude-dev.env not found at ${ENV_FILE}. See CLAUDE-DEV-ENVIRONMENT.md for required contents."
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

require_var() {
    local var="$1"
    if [[ -z "${!var:-}" ]]; then
        die "required variable '${var}' is not set in ${ENV_FILE}."
    fi
}

require_var GH_OWNER
require_var GH_REPO
require_var DEVENV_IMAGE

export GH_OWNER GH_REPO

# ----------------------------------------------------------------------
# Retrieve auth tokens from the host Secret Service keyring
# ----------------------------------------------------------------------
keyring_lookup() {
    local account="$1"
    local value
    value="$(secret-tool lookup service claude-dev account "$account" || true)"
    if [[ -z "$value" ]]; then
        die "no secret found in keyring for service=claude-dev account=${account}. See CLAUDE-DEV-ENVIRONMENT.md for the bootstrap procedure."
    fi
    printf '%s' "$value"
}

CLAUDE_CODE_OAUTH_TOKEN="$(keyring_lookup claude-oauth)"
GH_TOKEN="$(keyring_lookup github-token)"
export CLAUDE_CODE_OAUTH_TOKEN GH_TOKEN

# ----------------------------------------------------------------------
# Detect host timezone
# ----------------------------------------------------------------------
detect_host_tz() {
    if [[ -f /etc/timezone ]]; then
        cat /etc/timezone
    elif [[ -L /etc/localtime ]]; then
        readlink -f /etc/localtime | sed 's|.*/zoneinfo/||'
    else
        echo "UTC"
    fi
}

TZ="$(detect_host_tz)"
export TZ

# ----------------------------------------------------------------------
# Build docker run argument list
# ----------------------------------------------------------------------
DOCKER_ARGS=(
    run --rm -it
    -e GH_OWNER -e GH_REPO
    -e CLAUDE_CODE_OAUTH_TOKEN -e GH_TOKEN
    -e TZ
)

if [[ -n "$ISSUE_ID" ]]; then
    export ISSUE_ID
    DOCKER_ARGS+=(-e ISSUE_ID)
fi

# Local image tag for v0; switch to digest-pinned GHCR reference at Step 13.
DOCKER_ARGS+=("${DEVENV_IMAGE}:dev")

# If a command override was given, append it after the image reference.
# Docker passes everything after the image to the container's CMD, which
# the entrypoint exec's via "$@".
if [[ ${#CMD_OVERRIDE[@]} -gt 0 ]]; then
    DOCKER_ARGS+=("${CMD_OVERRIDE[@]}")
fi

# ----------------------------------------------------------------------
# Run
# ----------------------------------------------------------------------
exec docker "${DOCKER_ARGS[@]}"
