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
# The default command is whatever the image's CMD specifies (claude).
# The override is intended for troubleshooting (e.g., running
# `uv run pytest` against a fresh clone without entering an interactive
# session).
#
# [TODO] Hardening flags, GHCR pull, digest pinning, entrypoint logic, and
# pre-exit reporting are added in later steps.
# ======================================================================

set -euo pipefail

# ----------------------------------------------------------------------
# Locate required directories and files
# ----------------------------------------------------------------------
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}")"
PROJECT_DIR="$( cd "${SCRIPT_DIR}/.." && pwd )"

ENV_FILE="${SCRIPT_DIR}/claude-dev.env"
ENVOY_DIR="${PROJECT_DIR}/.devcontainer/envoy"
ENVOY_TEMPLATE="${ENVOY_DIR}/envoy.yaml.template"

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
                 context.

  -- <cmd>...    Optional. Override the image's default command.

Examples:
  claude-dev.sh                              # session with no Issue
  claude-dev.sh 42                           # session for Issue #42
  claude-dev.sh -- ls -la /workspace         # one-off ls, no Issue
  claude-dev.sh 42 -- uv run pytest -q       # one-off pytest for Issue #42
EOF
}

require_tool() {
    local tool="$1"
    local hint="$2"
    if ! command -v "$tool" >/dev/null 2>&1; then
        die "required tool '$tool' not found in PATH. ${hint}"
    fi
}

require_var() {
    local var="$1"
    if [[ -z "${!var:-}" ]]; then
        die "required variable '${var}' is not set in ${ENV_FILE}."
    fi
}

quote_command() {
    printf '%q ' "$@"
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
require_tool docker      "Install Docker Engine (https://docs.docker.com/engine/install/)."
require_tool secret-tool "Install libsecret-tools (apt install libsecret-tools)."
require_tool tmux        "Install tmux (apt install tmux)."
require_tool openssl     "Install OpenSSL (apt install openssl)."

# ----------------------------------------------------------------------
# Load and validate claude-dev.env
# ----------------------------------------------------------------------
if [[ ! -f "$ENV_FILE" ]]; then
    die "claude-dev.env not found at ${ENV_FILE}. See CLAUDE-DEV-ENVIRONMENT.md for required contents."
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

require_var GH_OWNER
require_var GH_REPO
require_var DEVENV_IMAGE
require_var ENVOY_IMAGE
require_var ENVOY_ADMIN_HOST_PORT
require_var ENVOY_ADMIN_CONTAINER_PORT
require_var ENVOY_ADMIN_ADDRESS
require_var ENVOY_SOCKET_CONTAINER_PATH

export GH_OWNER GH_REPO

# ----------------------------------------------------------------------
# If not already inside tmux, re-enter this launcher inside a tmux session.
#
# This differs from the original script, which ran docker directly as the
# tmux command. Running the launcher itself inside tmux lets us keep Envoy
# lifecycle cleanup in the same process as the Claude container run.
# ----------------------------------------------------------------------
if [[ -z "${TMUX:-}" ]]; then
    SUFFIX="$(openssl rand -hex 2)"
    if [[ -n "$ISSUE_ID" ]]; then
        TMUX_SESSION="${GH_OWNER}-${GH_REPO}-${ISSUE_ID}-${SUFFIX}"
    else
        TMUX_SESSION="${GH_OWNER}-${GH_REPO}-${SUFFIX}"
    fi

    echo "tmux session: ${TMUX_SESSION}"

    TMUX_COMMAND="$(quote_command "$SCRIPT_PATH" "$@")"
    exec tmux new-session -s "${TMUX_SESSION}" "${TMUX_COMMAND}"
fi

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
# Envoy sidecar runtime setup
# ----------------------------------------------------------------------
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$(openssl rand -hex 8)"
RUN_BASE="${XDG_RUNTIME_DIR:-/tmp}/claude-dev"
RUN_DIR="${RUN_BASE}/${RUN_ID}"

ENVOY_CONTAINER="claude-dev-envoy-${RUN_ID}"
ENVOY_RUNTIME_CONFIG="${RUN_DIR}/envoy.yaml"

cleanup_envoy() {
    local status=$?
    trap - EXIT INT TERM

    if [[ -n "${ENVOY_CONTAINER:-}" ]]; then
        docker stop "${ENVOY_CONTAINER}" >/dev/null 2>&1 || true
    fi

    if [[ -n "${RUN_DIR:-}" ]]; then
        rm -rf "${RUN_DIR}" >/dev/null 2>&1 || true
    fi

    exit "$status"
}

trap cleanup_envoy EXIT INT TERM

prepare_envoy() {
    if [[ ! -f "$ENVOY_TEMPLATE" ]]; then
        die "Envoy config template not found at ${ENVOY_TEMPLATE}"
    fi

    mkdir -p "$RUN_DIR"
    chmod 700 "$RUN_DIR"

    sed \
        -e "s|__ENVOY_SOCKET_PATH__|${ENVOY_SOCKET_CONTAINER_PATH}|g" \
        -e "s|__ENVOY_ADMIN_ADDRESS__|${ENVOY_ADMIN_ADDRESS}|g" \
        -e "s|__ENVOY_ADMIN_PORT__|${ENVOY_ADMIN_CONTAINER_PORT}|g" \
        "$ENVOY_TEMPLATE" > "$ENVOY_RUNTIME_CONFIG"

    chmod 600 "$ENVOY_RUNTIME_CONFIG"
}

start_envoy() {
    prepare_envoy

    echo "Starting Envoy perimeter sidecar: ${ENVOY_CONTAINER}"
    echo "Envoy admin UI: http://127.0.0.1:${ENVOY_ADMIN_HOST_PORT}/"

    docker run --rm -d \
        --name "${ENVOY_CONTAINER}" \
        --user "$(id -u):$(id -g)" \
        --cap-drop ALL \
        --security-opt no-new-privileges \
        --read-only \
        --tmpfs /tmp:rw,nosuid,nodev,noexec,size=16m \
        -p "127.0.0.1:${ENVOY_ADMIN_HOST_PORT}:${ENVOY_ADMIN_CONTAINER_PORT}" \
        -v "${RUN_DIR}:/run/claude-dev-proxy:rw" \
        "${ENVOY_IMAGE}" \
        -c /run/claude-dev-proxy/envoy.yaml
}

wait_for_envoy() {
    local socket_host_path="${RUN_DIR}/$(basename "$ENVOY_SOCKET_CONTAINER_PATH")"

    for _ in {1..100}; do
        if [[ -S "$socket_host_path" ]]; then
            echo "Envoy proxy socket ready: ${socket_host_path}"
            return 0
        fi

        if ! docker inspect -f '{{.State.Running}}' "${ENVOY_CONTAINER}" >/dev/null 2>&1; then
            docker logs "${ENVOY_CONTAINER}" >&2 || true
            die "Envoy container exited before creating proxy socket"
        fi

        sleep 0.1
    done

    docker logs "${ENVOY_CONTAINER}" >&2 || true
    die "Envoy did not create proxy socket at ${socket_host_path}"
}

# ----------------------------------------------------------------------
# Build Claude container docker run argument list
#
# Intentionally unchanged for this draft. We are only validating that the
# Envoy sidecar can start, expose admin, and be cleaned up correctly.
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
start_envoy
wait_for_envoy

echo "Starting Claude dev container..."
docker "${DOCKER_ARGS[@]}"
