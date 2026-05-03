---
name: new-issue
description: Create a new GitHub Issue in the correct initial triage state for this project's agentic SDLC. Applies one type label (`feature`, `bug`, `chore`, or `docs`) plus `phase: triage` so the Project Manager can pick it up for Phase 1 triage. Invoke whenever the Project Owner asks to file, open, create, log, or track a new issue/bug/feature/chore/docs ticket — even when they don't say "issue" explicitly (e.g. "let's track X as a chore", "file a bug about Y", "open a ticket for the Z docs change").
---

# New Issue

This skill creates a new GitHub Issue in the state expected by the agentic SDLC defined in `docs/AGENTIC-SDLC.md`. It is a **Project Owner helper skill** — invoke it only when the Project Owner explicitly asks to create an Issue, never autonomously as part of phase execution.

## Why this skill exists

Phase 1 (Triage) of the SDLC requires every Issue to enter the system with:
- Exactly one **type label**: `feature`, `bug`, `chore`, or `docs`.
- The phase label `phase: triage`.

Issues created without these labels stall the workflow because the PM cannot derive what to do next from the Issue's GitHub state. This skill exists so a freshly created Issue is *immediately* in a state the PM can act on, with no manual cleanup in the GitHub Web UI — saving the Project Owner a context switch out of the PM session.

## Inputs

Collect three things from the Project Owner before creating the Issue:

1. **Type** — one of `feature`, `bug`, `chore`, `docs`. Their meanings (from the SDLC):
   - `feature` — new functionality
   - `bug` — defect fix
   - `chore` — non-functional work (CI, dependencies, configuration, releases)
   - `docs` — documentation-only changes
2. **Title** — a single-line description of the Issue.
3. **Body** (optional) — free-form markdown details.

If the Project Owner gives you a description but not a type, **ask**. Don't guess: picking the wrong type misroutes the Issue through the SDLC (e.g. `docs`-typed Issues skip Phases 3–6, so misclassifying a feature as `docs` would break the workflow).

If the description spans multiple lines, treat the first line as the title and fold the rest into the body. The GitHub Issue title field is single-line and asking the Project Owner to restructure their input is friction we don't need.

## Creating the Issue

Use the `gh` CLI. The repo has no GitHub MCP server configured, and `gh` is the supported primitive for `github:write` operations in this project.

```bash
gh issue create \
  --title "<title>" \
  --body "<body, or empty string if none>" \
  --label "<type>" \
  --label "phase: triage"
```

Both labels go in the same call so the Issue is never visible in an intermediate single-labelled state.

`gh issue create` prints the URL of the created Issue on success. Capture it and parse the Issue number from the trailing path segment (e.g. `https://github.com/owner/repo/issues/73` → `#73`).

## Reporting back

Report to the Project Owner:
- Issue number (e.g. `#73`).
- Issue URL.
- The two labels that were applied (the chosen type and `phase: triage`).

That is all. Do **not**:
- Drive triage. The PM does that next, and only when the Project Owner explicitly asks (e.g. "let's triage #73").
- Create a branch or any spec/design/plan files. Those are Phase 2+ artifacts.
- Open a PR.
- Call the `Validate Issue` skill — the Issue was just created by you with both required labels, so validation would be redundant.

## Body content guidance

Pass through whatever optional details the Project Owner provided, verbatim. If they provided nothing, leave the body empty.

Do **not** auto-fill structured sections (problem statement, acceptance criteria, reproduction steps, etc.). Two reasons:
- The repo's `.github/ISSUE_TEMPLATE/*.md` files exist for *external* contributors who need scaffolding. The Project Owner's internal flow is different — they have direct access to the PM and will hand-craft the structured content in Phase 2.
- Phase 2 captures structured scope and rationale in `docs/{issue-id}-{slug}/spec.md`. Pre-filling the Issue body with similar headings creates two divergent sources of truth that immediately drift apart.

## Failure handling

Surface failures clearly and stop. Do not paper over them — these are usually configuration issues that the Project Owner needs to fix outside this skill, and silent retries can produce duplicate Issues or hide setup gaps.

- **Missing labels.** If `gh issue create` fails because `feature`/`bug`/`chore`/`docs` or `phase: triage` doesn't exist in the repo, report which label is missing and stop. Provisioning labels is project-setup work, intentionally out of scope here.
- **`gh` unauthenticated or wrong repo.** Report the verbatim error and stop.
- **API failure.** Report the error and stop. Do not retry — repeated retries on an unclear failure can create duplicate Issues.

## Multiple Issues in one ask

If the Project Owner asks to create several Issues in one message ("create issues for X, Y, and Z"), invoke this skill once per Issue, sequentially. Confirm the type for each one if not given. Do not batch them into a single `gh` call — there isn't one, and one-per-Issue keeps reporting and failure handling clean.

## Examples

**Example 1 — type provided:**

> Project Owner: "create a new feature issue: support AVIF input in the jpegify command"

Run:
```bash
gh issue create --title "support AVIF input in the jpegify command" --body "" --label "feature" --label "phase: triage"
```
Reply: "Created #73 — https://github.com/owner/repo/issues/73 — with labels `feature` and `phase: triage`."

**Example 2 — type missing, ask first:**

> Project Owner: "open an issue: rawtherapee times out on large RAW files"

Reply: "Should this be a `bug` (defect in current behavior) or a `feature` (new behavior)?"

> Project Owner: "bug"

Then proceed as in Example 1 with `--label "bug"`.

**Example 3 — multi-line description:**

> Project Owner: "new chore: bump pre-commit hook versions. The repo is pinned to versions from 2024 and we should refresh to current."

Title: `bump pre-commit hook versions`
Body: `The repo is pinned to versions from 2024 and we should refresh to current.`
Labels: `chore` and `phase: triage`.
