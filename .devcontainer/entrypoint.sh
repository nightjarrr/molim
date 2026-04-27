#!/bin/bash
# ======================================================================
# entrypoint.sh — Claude Code dev environment bootstrap (Phase 2, Step 6)
#
# Runs as the container's ENTRYPOINT. Receives configuration via env
# vars from the launcher (claude-dev.sh on the host):
#   GH_OWNER, GH_REPO            project identity
#   GH_TOKEN                     GitHub Token (read/write per scoping)
#   CLAUDE_CODE_OAUTH_TOKEN      consumed later by claude itself
#   TZ                           host timezone
#   ISSUE_ID                     optional GitHub Issue number
#
# Organized into two logical sections:
#   1. BASE — generic Claude Code dev environment bootstrap
#   2. PROJECT — molim-specific dependency installation
#
# Eventually the BASE section will be extracted into a separately-
# published base image's entrypoint; for now both live here.
#
# Firewall installation and self-test are added in Phase 3.
# ======================================================================

set -euo pipefail

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
section() {
    printf '\n==> %s\n' "$*"
}

die() {
    echo "Error: $*" >&2
    exit 1
}


# ======================================================================
# BASE — generic Claude Code dev environment bootstrap
# ======================================================================

# ----------------------------------------------------------------------
# Validate required environment
# ----------------------------------------------------------------------
section "Validating environment"

require_env() {
    local var="$1"
    if [[ -z "${!var:-}" ]]; then
        die "required environment variable '${var}' is not set; check the launcher."
    fi
}

require_env GH_OWNER
require_env GH_REPO
require_env GH_TOKEN
require_env CLAUDE_CODE_OAUTH_TOKEN
require_env TZ

echo "GH_OWNER=${GH_OWNER}"
echo "GH_REPO=${GH_REPO}"
echo "TZ=${TZ}"
if [[ -n "${ISSUE_ID:-}" ]]; then
    echo "ISSUE_ID=${ISSUE_ID}"
else
    echo "ISSUE_ID=(not set; no specific Issue context)"
fi

# ----------------------------------------------------------------------
# Verify /workspace is empty
# A non-empty /workspace means the container deviates from design
# (a bind mount, a stale tmpfs, etc.); fail loudly rather than risk
# clobbering or merging unexpected content.
# ----------------------------------------------------------------------
section "Verifying /workspace is empty"

if [[ -n "$(ls -A /workspace 2>/dev/null)" ]]; then
    die "/workspace is not empty. Container is in an unexpected state; aborting."
fi
echo "/workspace is clean"

# ----------------------------------------------------------------------
# Configure GitHub authentication via gh
# This installs gh's git credential helper as a side effect, so both
# `gh` and `git` work against github.com without further setup.
# ----------------------------------------------------------------------
section "Configuring GitHub authentication"

GH_TOKEN_TMP="$GH_TOKEN"
unset GH_TOKEN
echo "$GH_TOKEN_TMP" | gh auth login --with-token --hostname github.com
unset GH_TOKEN_TMP
gh auth setup-git
gh auth status

# ----------------------------------------------------------------------
# Configure git identity
# Author is "Claude Code (authorized by <gh-user>)", email uses GitHub's
# noreply format keyed by the human's numeric user ID so the avatar
# routes to the human's profile.
# ----------------------------------------------------------------------
section "Configuring git identity"

GH_USER_ID="$(gh api user --jq .id)"
GH_USERNAME="$(gh api user --jq .login)"
GIT_AUTHOR_NAME="Claude Code (authorized by ${GH_USERNAME})"
GIT_AUTHOR_EMAIL="${GH_USER_ID}+${GH_USERNAME}@users.noreply.github.com"

git config --global user.name  "${GIT_AUTHOR_NAME}"
git config --global user.email "${GIT_AUTHOR_EMAIL}"

echo "Author: ${GIT_AUTHOR_NAME} <${GIT_AUTHOR_EMAIL}>"

# ----------------------------------------------------------------------
# Clone the project repository
# ----------------------------------------------------------------------
section "Cloning ${GH_OWNER}/${GH_REPO} into /workspace"

git clone "https://github.com/${GH_OWNER}/${GH_REPO}.git" /workspace
cd /workspace

# ----------------------------------------------------------------------
# Resolve and check out the working branch
#
#   ISSUE_ID not set                     -> stay on main
#   ISSUE_ID set, no linked branch       -> stay on main
#   ISSUE_ID set, one linked branch      -> check it out
#   ISSUE_ID set, multiple linked         -> refuse and exit
# ----------------------------------------------------------------------
section "Resolving working branch"

if [[ -z "${ISSUE_ID:-}" ]]; then
    echo "No ISSUE_ID; staying on main."
else
    LINKED_BRANCHES_JSON="$(gh issue develop "${ISSUE_ID}" --list --repo "${GH_OWNER}/${GH_REPO}" --json name 2>/dev/null || echo '[]')"
    LINKED_COUNT="$(echo "${LINKED_BRANCHES_JSON}" | jq 'length')"

    case "${LINKED_COUNT}" in
        0)
            echo "Issue #${ISSUE_ID}: no linked branch yet; staying on main."
            echo "Branch creation is the SDLC's spec phase responsibility."
            ;;
        1)
            BRANCH="$(echo "${LINKED_BRANCHES_JSON}" | jq -r '.[0].name')"
            echo "Issue #${ISSUE_ID}: one linked branch (${BRANCH}); checking out."
            git checkout "${BRANCH}"
            ;;
        *)
            echo "Issue #${ISSUE_ID}: multiple linked branches found:" >&2
            echo "${LINKED_BRANCHES_JSON}" | jq -r '.[].name' | sed 's/^/  - /' >&2
            die "ambiguous branch state. Resolve in GitHub (Issue page → Development sidebar → unlink unwanted branches) and retry."
            ;;
    esac
fi


# ======================================================================
# PROJECT — molim-specific dependency installation
# ======================================================================

# ----------------------------------------------------------------------
# Install Python and project dependencies via uv
# uv resolves Python from the project's .python-version /
# pyproject.toml, then installs locked deps from uv.lock.
# --frozen ensures no resolution against package registries.
# ----------------------------------------------------------------------
section "Installing project dependencies via uv sync"

uv sync --frozen


# ======================================================================
# COMMON — handoff to CMD
# ======================================================================

section "Bootstrap complete"

if [[ -n "${ISSUE_ID:-}" ]]; then
    ISSUE_TITLE="$(gh issue view "${ISSUE_ID}" --repo "${GH_OWNER}/${GH_REPO}" --json title --jq .title 2>/dev/null || echo '(unable to fetch)')"
    echo "Issue: #${ISSUE_ID} — ${ISSUE_TITLE}"
fi
echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
COMMITS_AHEAD="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
if [[ "${COMMITS_AHEAD}" -gt 0 ]]; then
    echo "Commits ahead of origin/main: ${COMMITS_AHEAD}"
fi
echo

# Hand off to whatever the image's CMD specifies (bash for Step 6,
# tmux+claude for Step 7).
exec "$@"
