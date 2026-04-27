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
#   claude-dev.sh                  # no issue; for "New Issue" skill or general session
#   claude-dev.sh <issue-id>       # work on a specific GitHub Issue
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
Usage: claude-dev.sh [<issue-id>]

  <issue-id>   Optional. Positive integer GitHub Issue number to work on.
               If omitted, the container starts without a specific Issue
               context (suitable for the "New Issue" skill or general work).

Examples:
  claude-dev.sh          # start a session with no issue context
  claude-dev.sh 42       # start a session for Issue #42
EOF
}

# ----------------------------------------------------------------------
# Argument validation
# ----------------------------------------------------------------------
if [[ $# -gt 1 ]]; then
    usage
    die "expected 0 or 1 arguments, got $#"
fi

ISSUE_ID=""
if [[ $# -eq 1 ]]; then
    if [[ ! "$1" =~ ^[1-9][0-9]*$ ]]; then
        usage
        die "issue ID must be a positive integer, got '$1'"
    fi
    ISSUE_ID="$1"
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

# ----------------------------------------------------------------------
# Run
# ----------------------------------------------------------------------
exec docker "${DOCKER_ARGS[@]}"
