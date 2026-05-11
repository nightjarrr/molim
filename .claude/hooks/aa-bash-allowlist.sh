#!/usr/bin/env bash
# PreToolUse hook for Associate Architect — restricts Bash tool invocations to the allowlist.
# Reads the Bash tool input JSON from stdin, extracts the command, and exits 0 (allow) or 2 (block).
#
# Allowlist:
#   git <anything>
#   gh issue view <anything>
#   gh issue develop <anything>
#   node scripts/add-changelog-entry.mjs <anything>

set -euo pipefail

command_str="$(jq -r '.command' <&0)"

# git <anything>
if [[ "$command_str" == git\ * || "$command_str" == "git" ]]; then
    exit 0
fi

# gh issue view <anything>
if [[ "$command_str" == "gh issue view "* ]]; then
    exit 0
fi

# gh issue develop <anything>  (Phase 2 branch creation)
if [[ "$command_str" == "gh issue develop "* ]]; then
    exit 0
fi

# node scripts/add-changelog-entry.mjs <anything>
if [[ "$command_str" == "node scripts/add-changelog-entry.mjs"* ]]; then
    exit 0
fi

echo "Blocked: Associate Architect is not permitted to run: $command_str" >&2
echo "Allowed commands: git, gh issue view, gh issue develop, node scripts/add-changelog-entry.mjs" >&2
exit 2
