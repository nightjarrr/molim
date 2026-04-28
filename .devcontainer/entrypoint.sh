#!/bin/bash
# ======================================================================
# entrypoint.sh — Claude Code dev environment bootstrap
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
#   ISSUE_ID not set                       -> stay on main
#   ISSUE_ID set, issue does not exist     -> error
#   ISSUE_ID set, issue exists, 0 branches -> stay on main
#   ISSUE_ID set, issue exists, 1 branch   -> check it out
#   ISSUE_ID set, issue exists, ≥2 branches -> refuse and exit
#
# Implemented via GraphQL because `gh issue develop --list` does not
# support --json output. The first:2 cap is sufficient since logic
# only distinguishes 0 / 1 / multiple.
# ----------------------------------------------------------------------
section "Resolving working branch"

if [[ -z "${ISSUE_ID:-}" ]]; then
    echo "No ISSUE_ID; staying on main."
else

    if ! gh issue view "${ISSUE_ID}" --repo "${GH_OWNER}/${GH_REPO}" --json number >/dev/null 2>&1; then
        die "Issue #${ISSUE_ID} not found in ${GH_OWNER}/${GH_REPO}."
    fi

    QUERY_RESULT="$(gh api graphql \
        -F owner="${GH_OWNER}" \
        -F repo="${GH_REPO}" \
        -F number="${ISSUE_ID}" \
        -f query='
            query($owner: String!, $repo: String!, $number: Int!) {
              repository(owner: $owner, name: $repo) {
                issue(number: $number) {
                  linkedBranches(first: 2) {
                    nodes { ref { name } }
                  }
                }
              }
            }')"

    # Issue not found -> .data.repository.issue is null
    if [[ "$(echo "${QUERY_RESULT}" | jq '.data.repository.issue')" == "null" ]]; then
        die "Issue #${ISSUE_ID} not returned by GraphQL API in ${GH_OWNER}/${GH_REPO}."
    fi

    LINKED_BRANCHES="$(echo "${QUERY_RESULT}" | jq -r '.data.repository.issue.linkedBranches.nodes | map(.ref.name)')"
    LINKED_COUNT="$(echo "${LINKED_BRANCHES}" | jq 'length')"

    case "${LINKED_COUNT}" in
        0)
            echo "Issue #${ISSUE_ID}: no linked branch yet; staying on main."
            echo "Branch creation is the SDLC's spec phase responsibility."
            ;;
        1)
            BRANCH="$(echo "${LINKED_BRANCHES}" | jq -r '.[0]')"
            echo "Issue #${ISSUE_ID}: one linked branch (${BRANCH}); checking out."
            git checkout "${BRANCH}"
            ;;
        *)
            echo "Issue #${ISSUE_ID}: multiple linked branches found:" >&2
            echo "${LINKED_BRANCHES}" | jq -r '.[]' | sed 's/^/  - /' >&2
            die "ambiguous branch state. Resolve in GitHub (Issue page → Development sidebar → unlink unwanted branches) and retry."
            ;;
    esac
fi

# ----------------------------------------------------------------------
# Write ~/.claude.json
# Suppresses the first-run onboarding wizard (theme picker, login method
# screen). hasCompletedOnboarding is the gate; lastOnboardingVersion
# must match the installed Claude Code version. Template lives at
# /etc/claude-dev/.claude.json.template (baked into the image); we stamp 
# in the version and write to the home dir.
# ----------------------------------------------------------------------
section "Writing ~/.claude.json"
sed "s/__CLAUDE_CODE_VERSION__/${CLAUDE_CODE_VERSION}/" \
    /etc/claude-dev/.claude.json.template > "${HOME}/.claude.json"
chmod 600 "${HOME}/.claude.json"
echo "lastOnboardingVersion: ${CLAUDE_CODE_VERSION}"


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

# Hand off to the image's CMD (claude).
exec "$@"
