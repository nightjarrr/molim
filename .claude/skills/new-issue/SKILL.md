---
name: new-issue
description: Create a new GitHub Issue in the correct initial triage state for this project's agentic SDLC. Applies one type label (`feature`, `bug`, `chore`, or `docs`) plus `phase: triage`. Invoked manually by the user, never by the model.
disable-model-invocation: true
context: fork
model: Haiku
allowed-tools: Bash(gh issue create), AskUserQuestion
---

# New Issue

This skill creates a new GitHub Issue in the initial state of the SDLC.

## Why this skill exists

Phase 1 (Triage) of the SDLC requires every Issue to enter the system with:
- Exactly one **type label**: `feature`, `bug`, `chore`, or `docs`.
- The phase label `phase: triage`.

## Inputs

You need to obtain three things from the user before creating the Issue:

1. **Type** — one of `feature`, `bug`, `chore`, `docs`. Their meanings (from the SDLC):
   - `feature` — new functionality
   - `bug` — defect fix
   - `chore` — non-functional work (CI, dependencies, configuration, releases)
   - `docs` — documentation-only changes
2. **Title** — a single-line description of the Issue in sentence case: first word capitalized, rest lowercase unless proper nouns.
3. **Body** (optional) — free-form markdown details.

The user can give you all or some of this information as input to the skill. In case both type and title are provided, you can proceed to creation immediately, without additional interactions with the user.

If the user gives you a description but not a type, **ask**. Don't guess: picking the wrong type misroutes the Issue through the SDLC.

If the description spans multiple lines, create the title by summarizing the description into 3-7 words. Use the whole description as the issue body. The GitHub Issue title field is single-line and asking the user to restructure their input is friction we don't need.

If the user's input begins with a `type:` prefix (e.g. `chore: bump pre-commit hook versions`), strip that prefix before using the text as the title or body — the type is already captured via the label.

### When invoked with no input

If the user calls `/new-issue` with no arguments, **your first action is to start the guided flow and call `AskUserQuestion` immediately** — do not describe what you are about to do, do not list the steps, just invoke the tool with the following:
- Question: "What type of issue is this?"
- Options: `feature` (new functionality), `bug` (defect fix), `chore` (non-functional work), `docs` (documentation-only)

After receiving the type, ask for the title in plain text.
After receiving the title, call `AskUserQuestion` for the body step with two options:
 - "Create now" — create the issue immediately with an empty body and type, title captured earlier.
 - "Add details first" — ask in plain text: "What should the body say?", capture user input,then create the issue with that text as the body and type, title captured earlier.

One question per turn — never ask more than one at a time.

## Creating the Issue

Use the `gh` CLI. The command should look like:

```bash
gh issue create \
  --title "<title>" \
  --body "<body, or empty string if none>" \
  --label "<type>" \
  --label "phase: triage"
```

Both labels go in the same call as separate --label "<value>" switches.

`gh issue create` prints the URL of the created Issue on success. Capture it and parse the Issue number from the trailing path segment (e.g. `https://github.com/owner/repo/issues/73` → `#73`).

Once you have all the necessary inputs, use the `Bash` tool to run `gh issue create` directly — do not attempt to re-invoke this skill via the Skill tool. This skill has `disable-model-invocation: true`, meaning the model cannot trigger it; doing so will fail silently and interrupt the flow.

## Reporting back

Report to the user:
- Issue number (e.g. `#73`).
- Issue URL.
- The two labels that were applied (the chosen type and `phase: triage`).

That is all. Do **not**:
- Drive triage.
- Create a branch or any spec/design/plan files.
- Open a PR.
- Call other skills.

## Body content guidance

Pass through whatever optional details the user provided, verbatim. If they provided nothing, leave the body empty.

Do **not** auto-fill structured sections (problem statement, acceptance criteria, reproduction steps, etc.).

## Failure handling

Surface failures clearly and stop. Do not paper over them — these are usually configuration issues that the user needs to fix outside this skill, and silent retries can produce duplicate Issues or hide setup gaps.

- **Missing labels.** If `gh issue create` fails because `feature`/`bug`/`chore`/`docs` or `phase: triage` doesn't exist in the repo, report which label is missing and stop. Provisioning labels is project-setup work, intentionally out of scope here. If `ensure-github-labels` skill is available, suggest that the user uses it to create the required labels.
- **`gh` unauthenticated or wrong repo.** Report the verbatim error and stop.
- **API failure.** Report the error and stop. Do not retry — repeated retries on an unclear failure can create duplicate Issues.

## Examples

**Example 1 — type provided:**

> Project Owner: "/new-issue feature: support AVIF input in the jpegify command"

Run:
```bash
gh issue create --title "Support AVIF input in the jpegify command" --body "" --label "feature" --label "phase: triage"
```
Reply: "Created #73 — https://github.com/owner/repo/issues/73 — with labels `feature` and `phase: triage`."

**Example 2 — type missing, ask first:**

> Project Owner: "/new-issue rawtherapee times out on large RAW files"

Reply: "Should this be a `bug` (defect in current behavior) or a `feature` (new behavior)?"

> Project Owner: "bug"

Then proceed as in Example 1 with `--label "bug"`.

**Example 3 — multi-line description:**

> Project Owner: "/new-issue chore: bump pre-commit hook versions. The repo is pinned to versions from 2024 and we should refresh to current."

Title: `Refresh pre-commit hook versions to current versions`
Body: `Bump pre-commit hook versions. The repo is pinned to versions from 2024 and we should refresh to current.`
Labels: `chore` and `phase: triage`.

**Example 4 — no arguments:**

> Project Owner: "/new-issue"

Use `AskUserQuestion`:
- Question: "What type of issue is this?"
- Options: `feature` (new functionality), `bug` (defect fix), `chore` (non-functional work), `docs` (documentation-only)

> Project Owner selects: `chore`

Ask in plain text: "What should the issue title be?"

> Project Owner: "Refresh pre-commit hook versions"

Use `AskUserQuestion`:
- Question: "Ready to create, or would you like to add body details first?"
- Options: "Create now" (empty body), "Add details first"

> Project Owner selects: "Create now"

Run:
```bash
gh issue create --title "Refresh pre-commit hook versions" --body "" --label "chore" --label "phase: triage"
```
Reply: "Created #74 — https://github.com/owner/repo/issues/74 — with labels `chore` and `phase: triage`."

**Example 5 — no arguments, with body:**

Steps 1 and 2 are the same as Example 4. At step 3, the user selects "Add details first":

Ask in plain text: "What should the body say?"

> Project Owner: "The repo is pinned to versions from 2024 and we should refresh to current."

Run:
```bash
gh issue create --title "Refresh pre-commit hook versions" --body "The repo is pinned to versions from 2024 and we should refresh to current." --label "chore" --label "phase: triage"
```
Reply: "Created #74 — https://github.com/owner/repo/issues/74 — with labels `chore` and `phase: triage`."
