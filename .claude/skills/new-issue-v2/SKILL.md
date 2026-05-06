---
name: new-issue-v2
description: Create a new GitHub issue in the correct initial triage state for this project's agentic SDLC. Applies one type label (feature, bug, chore, or docs) plus phase: triage. Triggered by phrases like "create a new issue", "let's create an issue", "track this as an issue", "open an issue for this", "file a bug", "let's file an issue".
allowed-tools: Bash(gh issue create), AskUserQuestion
---

# New Issue (v2)

This skill creates a new GitHub issue in the initial state of the SDLC.

## Why this skill exists

Phase 1 (Triage) of the SDLC requires every issue to enter the system with:
- Exactly one **type label**: `feature`, `bug`, `chore`, or `docs`.
- The phase label `phase: triage`.

## Inputs

Three things are needed before creating the issue:

1. **Type** — one of `feature`, `bug`, `chore`, `docs`. Their meanings:
   - `feature` — new functionality
   - `bug` — defect fix
   - `chore` — non-functional work (CI, dependencies, configuration, releases)
   - `docs` — documentation-only changes
2. **Title** — a single-line description in sentence case: first word capitalized, rest lowercase unless proper nouns.
3. **Body** (optional) — free-form markdown details.

### Inferring from context

Before asking any questions, check the current conversation for information already provided:
- If the type is evident from context (e.g. the user said "there's a bug" or "I want a new feature"), use it without asking.
- If a title-worthy description is already present, propose it as the title rather than asking from scratch.
- If both type and title are clear from context, skip straight to the body step.

If the user's invocation provides type and title directly, proceed to creation without additional interaction.

### When details are missing

Work through the missing pieces one question at a time:

1. **Type unknown** — use `AskUserQuestion` with four options, one per type, each with its one-line description.
2. **Title unknown** — ask in plain text: "What should the issue title be?"
3. **Body** — use `AskUserQuestion` with two options:
   - "Create now" — create the issue immediately with an empty body.
   - "Add details first" — ask in plain text: "What should the body say?", then create with that text as the body.

Never ask more than one question at a time.

### Input parsing rules

- If the user gives a `type:` prefix (e.g. `chore: bump pre-commit hook versions`), strip the prefix before using the text as the title — the type is already captured via the label.
- If the description spans multiple lines, summarize it into a 3–7 word title and use the full description as the body. The GitHub issue title field is single-line.
- If the type is missing from a description, ask rather than guess — picking the wrong type misroutes the issue through the SDLC.

## Creating the issue

Use the `gh` CLI:

```bash
gh issue create \
  --title "<title>" \
  --body "<body, or empty string if none>" \
  --label "<type>" \
  --label "phase: triage"
```

Both labels go in the same call as separate `--label "<value>"` switches.

`gh issue create` prints the URL of the created issue on success. Parse the issue number from the trailing path segment (e.g. `https://github.com/owner/repo/issues/73` → `#73`).

## Reporting back

Report:
- Issue number (e.g. `#73`).
- Issue URL.
- The two labels applied (the chosen type and `phase: triage`).

Do **not**:
- Drive triage.
- Create a branch or any spec/design/plan files.
- Open a PR.
- Call other skills.

## Body content guidance

Pass through whatever optional details the user provided, verbatim. If they provided nothing, leave the body empty. Do not auto-fill structured sections.

## Failure handling

Surface failures clearly and stop. Do not paper over them or retry silently — these are usually configuration issues the user needs to fix, and silent retries can produce duplicate issues.

- **Missing labels.** If `gh issue create` fails because a required label doesn't exist, report which label is missing and stop. Suggest using the `ensure-github-labels` skill if it is available.
- **`gh` unauthenticated or wrong repo.** Report the verbatim error and stop.
- **API failure.** Report the error and stop.

## Examples

**Example 1 — type provided:**

> "let's create an issue: feature: support AVIF input in the jpegify command"

Run:
```bash
gh issue create --title "Support AVIF input in the jpegify command" --body "" --label "feature" --label "phase: triage"
```
Reply: "Created #73 — https://github.com/owner/repo/issues/73 — with labels `feature` and `phase: triage`."

**Example 2 — type missing, ask first:**

> "/new-issue-v2 rawtherapee times out on large RAW files"

Ask: "Should this be a `bug` (defect in current behavior) or a `feature` (new behavior)?"

> "bug"

Then proceed as in Example 1 with `--label "bug"`.

**Example 3 — multi-line description:**

> "/new-issue-v2 chore: bump pre-commit hook versions. The repo is pinned to versions from 2024 and we should refresh to current."

Title: `Bump pre-commit hook versions`
Body: `The repo is pinned to versions from 2024 and we should refresh to current.`
Labels: `chore` and `phase: triage`.

**Example 4 — no arguments:**

> "/new-issue-v2"

Use `AskUserQuestion`:
- Question: "What type of issue is this?"
- Options: `feature` (new functionality), `bug` (defect fix), `chore` (non-functional work), `docs` (documentation-only)

> selects: `chore`

Ask in plain text: "What should the issue title be?"

> "Refresh pre-commit hook versions"

Use `AskUserQuestion`:
- Question: "Ready to create, or would you like to add body details first?"
- Options: "Create now" (empty body), "Add details first"

> selects: "Create now"

Run:
```bash
gh issue create --title "Refresh pre-commit hook versions" --body "" --label "chore" --label "phase: triage"
```
Reply: "Created #74 — https://github.com/owner/repo/issues/74 — with labels `chore` and `phase: triage`."

**Example 5 — no arguments, with body:**

Steps 1 and 2 same as Example 4. At step 3, user selects "Add details first":

Ask: "What should the body say?"

> "The repo is pinned to versions from 2024 and we should refresh to current."

Run:
```bash
gh issue create --title "Refresh pre-commit hook versions" --body "The repo is pinned to versions from 2024 and we should refresh to current." --label "chore" --label "phase: triage"
```

**Example 6 — model-triggered with context inference:**

Earlier in the conversation the user said: "the ffmpeg timeout on large files is really annoying, we should track that"

> "track this as an issue"

Infer type=`bug` (defect in current behavior) and propose title from context: "FFmpeg times out on large files".

Use `AskUserQuestion`:
- Question: "Ready to create, or would you like to add body details first?"
- Options: "Create now" (empty body), "Add details first"

> selects: "Create now"

Run:
```bash
gh issue create --title "FFmpeg times out on large files" --body "" --label "bug" --label "phase: triage"
```
Reply: "Created #75 — https://github.com/owner/repo/issues/75 — with labels `bug` and `phase: triage`."
