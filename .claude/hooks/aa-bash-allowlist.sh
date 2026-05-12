#!/usr/bin/env bash
# PreToolUse hook for Associate Architect — restricts Bash tool invocations to the allowlist.
# Reads the Bash tool input JSON from stdin, extracts the command, and exits 0 (allow) or 2 (block).

set -euo pipefail

input=$(cat)

# Sanity check - only Bash tool supported.
# Block everything else to report miscongifuration early.
tool_name="$(echo "$input" | jq -r '.tool_name')"
if [[ "$tool_name" != "Bash" ]]; then
    echo "Invalid: Hook only supports Bash tool." >&2
    exit 2
fi

command_str="$(echo "$input" | jq -r '.tool_input.command')"

allowlist=(
    "git"
    "gh issue view"
    "gh issue list"
    "gh issue develop"
    "gh pr view"
    "gh pr diff"
    "node scripts/add-changelog-entry.mjs"
)

for pattern in "${allowlist[@]}"; do
    if [[ "$command_str" == "$pattern"* ]]; then
        exit 0
    fi
done

echo "Blocked: Associate Architect is not permitted to run: $command_str" >&2
echo "Allowed: ${allowlist[*]}" >&2
exit 2
