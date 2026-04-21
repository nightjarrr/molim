# Development Workflow

## Purpose and audience

This document describes the end-to-end development workflow for this project,
designed for AI-assisted development where the human Project Owner acts as product
owner / architect and an AI agent acts as developer.

It is a mandatory context document for every AI Agent session.

**If you are an AI Agent reading this:**
- This document governs how all development work is structured and executed
- You must follow the phase workflow, gate conditions, and linking
  requirements described here without deviation
- Before starting any task, read the current Issue's phase label to determine
  where work stands and whether prerequisites are met
- If a prerequisite phase has not been completed and accepted by the Project
  Owner, stop and report this — do not proceed
- When in doubt about scope or approach, surface the question to the Project
  Owner rather than making assumptions

**Other context documents you must read at the start of every session:**

| Document | Purpose |
|---|---|
| `docs/architecture.md` | Codebase structure, modules, and key patterns |
| `docs/conventions.md` | Coding conventions to follow in all code changes |

The current Issue and its phase label are your session entry point. The
`docs/{issue-id}-{slug}/` folder contains the artifacts produced so far for
that Issue — read all files present before acting.

---

## Roles

**Project Owner (human)**
- Only human can assume this role
- Defines requirements and priorities
- Reviews and approves all artifacts at each phase gate
- Makes architectural decisions
- Merges PRs
- Controls release versioning and pushes release tags

**AI Agent (developer)**
- Produces draft artifacts at each phase (spec, tech design, implementation plan)
- Implements code changes
- Updates project-wide documentation as part of each feature
- Generates changelog entries
- Reads Issue phase labels to determine current state before acting
- Short-circuits and reports to the Project Owner if phase prerequisites
  are not met

---

## Repository structure

```
docs/
├── architecture.md           # Persistent project-wide architecture reference
├── conventions.md            # Coding conventions and patterns
├── SDLC.md                   # This document — the development workflow
└── {issue-id}-{slug}/        # Per-feature folder, e.g. 42-avif-heic-support/
    ├── spec.md               # Functional specification
    ├── tech-design.md        # Technical design
    └── impl-plan.md          # Implementation plan

CHANGELOG.md                  # Running changelog with UPCOMING section
```

Branch naming: `feature/{issue-id}-{slug}`, `fix/{issue-id}-{slug}`,
`chore/{issue-id}-{slug}`, `docs/{issue-id}-{slug}`

---

## GitHub Issues

Issues are the tracking and planning layer. Substantive content lives in the
repo — Issues link to it.

### Type labels

| Label | Used for |
|---|---|
| `feature` | New functionality |
| `bug` | Defect fixes |
| `chore` | Non-functional work: CI, deps, configuration, releases |
| `docs` | Documentation-only changes |

### Phase labels

Phase labels track the current state of an Issue through the development
workflow. The AI Agent reads the phase label before starting any task and
short-circuits if the prerequisite phase has not been completed and accepted
by the Project Owner.

| Label | Meaning |
|---|---|
| `phase: triage` | Newly created, awaiting triage by Project Owner |
| `phase: spec` | Spec in progress or awaiting acceptance |
| `phase: tech-design` | Tech design in progress or awaiting acceptance |
| `phase: impl-plan` | Implementation plan in progress or awaiting acceptance |
| `phase: implementation` | Coding in progress |
| `phase: dev-done` | Implementation complete, documentation sweep done, PR open |
| `phase: released` | Merged and included in a release |

Only one phase label is active at a time. The AI Agent updates the phase
label as each phase is completed.

### Milestones

Each milestone corresponds to a planned release. Issues are assigned to
milestones for release planning. A milestone is closed when its corresponding
release tag is pushed.

### Issue ↔ PR ↔ branch linking

GitHub provides first-class linking between Issues, PRs, and branches that
the AI Agent uses throughout the workflow. This is more reliable than naming
conventions alone, which act only as a quick point of reference.

**Branch → Issue link**
When the AI Agent creates the feature branch in Phase 2, it links the branch
to the Issue via the GitHub API. This causes the branch to appear in the
Issue's Development sidebar, and GitHub tracks when the branch gets a PR
opened against it.

**PR → Issue link (closing keyword)**
When the AI Agent opens a PR in Phase 7, the PR description includes
`Closes #N` where N is the Issue number. This:
- Links the PR to the Issue in the Development sidebar of both
- Automatically closes the Issue when the PR is merged into `main`
- Creates a cross-reference event in the Issue timeline

No manual linking action is needed for the Issue-to-PR link — GitHub creates
it automatically when `Closes #N` appears in the PR description.

**Branch naming convention role**
The `{issue-id}-{slug}` pattern in branch names and `docs/` folder names
provides human readability and a back-reference from the folder to the Issue.
It is documentation and folder sequencing, not the primary linking mechanism — that is handled by
GitHub's Development panel and closing keywords as described above.

**AI Agent linking responsibilities summary**

| Action | When | How |
|---|---|---|
| Link branch to Issue | Phase 2, step 3 | GitHub API |
| Link PR to Issue + auto-close | Phase 7, step 1 | `Closes #N` in PR description |
| Update artifact links to `main` | Phase 7, step 7 | Edit Issue body via GitHub API |

---

## Feature workflow

### Phase 1 — Triage

**Trigger:** new Issue created (by the Project Owner, externally, or via
security report)

**Who:** Project Owner

**Steps:**
1. Review the Issue
2. Assign type label (`feature`, `bug`, `chore`, or `docs`) and milestone
3. If externally created: assess whether to accept — close with explanation
   referencing `CONTRIBUTING.md` if not
4. If a private security vulnerability: follow the security workflow (see
   below) before making the Issue public
5. Set phase label to `phase: spec`

**Gate:** Issue has a type label, milestone, and `phase: spec` label before
Phase 2 begins.

---

### Phase 2 — Functional specification

**Who:** Project Owner + AI Agent (collaborative)

**Prerequisite phase label:** `phase: spec`

**Output:** `docs/{issue-id}-{slug}/spec.md`

**Contents of spec.md:**
- Problem statement / motivation
- Functional requirements (what the feature does, from a user perspective)
- Out of scope (explicit exclusions)
- Acceptance criteria (how to verify it is done)
- Open questions (all resolved before Phase 3 begins)

**Steps:**
1. Project Owner starts a session with the AI Agent, providing the Issue and
   initial raw idea as input
2. AI Agent drafts the spec, Project Owner reviews, both iterate until Project
   Owner accepts it
3. AI Agent commits `spec.md` to a new branch: `feature/{issue-id}-{slug}`, and
   links the branch to the Issue via the GitHub API
4. AI Agent updates the Issue: adds a link to `spec.md`
5. AI Agent updates phase label to `phase: tech-design`

**Gate:** Project Owner explicitly accepts the spec. Phase label updated to
`phase: tech-design` before Phase 3 begins.

---

### Phase 3 — Technical design

**Who:** AI Agent

**Prerequisite phase label:** `phase: tech-design`

**Primary inputs:** `spec.md`, `docs/architecture.md`, relevant source files

**Output:** `docs/{issue-id}-{slug}/tech-design.md`

**Contents of tech-design.md:**
- Affected modules and files
- Data model changes (if any)
- Key design decisions and rationale
- Alternatives considered and rejected
- Dependencies or prerequisites introduced
- Impact on existing functionality

**Steps:**
1. AI Agent reads `spec.md`, `docs/architecture.md`, and relevant source
   files
2. AI Agent drafts the tech design, Project Owner reviews, both iterate until Project
   Owner accepts it
3. AI Agent commits `tech-design.md` to the feature branch
4. AI Agent updates the Issue: adds link to `tech-design.md`
5. AI Agent updates phase label to `phase: impl-plan`

**Gate:** Project Owner explicitly accepts the tech design. Phase label
updated to `phase: impl-plan` before Phase 4 begins.

---

### Phase 4 — Implementation plan

**Who:** AI Agent

**Prerequisite phase label:** `phase: impl-plan`

**Primary inputs:** `spec.md`, `tech-design.md`

**Output:** `docs/{issue-id}-{slug}/impl-plan.md`

**Contents of impl-plan.md:**
- Ordered list of implementation steps
- For each step: files to create/modify, classes/functions to add/change
- Test coverage plan: what new tests are required
- Estimated risk areas or complexity flags

**Steps:**
1. AI Agent reads `spec.md` and `tech-design.md`
2. AI Agent drafts the impl plan, Project Owner reviews, both iterate until Project
   Owner accepts it
3. AI Agent commits `impl-plan.md` to the feature branch
4. AI Agent updates the Issue: adds link to `impl-plan.md`
5. AI Agent updates phase label to `phase: implementation`

**Gate:** Project Owner explicitly accepts the implementation plan. Phase label updated
to `phase: implementation` before Phase 5 begins.

---

### Phase 5 — Implementation

**Who:** AI Agent

**Prerequisite phase label:** `phase: implementation`

**Primary inputs:** `impl-plan.md`, `tech-design.md`, `docs/architecture.md`,
`docs/conventions.md`

**Steps:**
1. AI Agent implements code changes per `impl-plan.md`
2. All existing tests must remain green
3. New tests per the test coverage plan in `impl-plan.md` must be written
   and passing
4. All quality gates must pass: `uv run pytest`, `ruff format --check`,
   `ruff check`
5. AI Agent flags any deviations from the impl plan to the Project Owner
   before proceeding

**Gate (DEV DONE):** all tests green, all quality gates passing, no
unresolved deviations from the impl plan.

---

### Phase 6 — Documentation sweep

**Who:** AI Agent

**Trigger:** DEV DONE gate reached

**Steps:**
1. AI Agent reviews `docs/architecture.md` — update if the feature changed anything
   structural
2. AI Agent reviews `README.md` — update if requirements, commands, or install
   instructions changed
3. AI Agent reviews `docs/conventions.md` — update if new patterns were introduced
4. AI Agent reviews any other project-wide docs that may be affected
5. AI Agent adds a new entry to the `UPCOMING` section of `CHANGELOG.md` (see
   changelog format below)
6. AI Agent commits all documentation updates to the feature branch
7. AI Agent updates phase label to `phase: dev-done`

**Gate:** Project Owner reviews all documentation changes as part of the
PR review (next phase, phase 7 - pull request).

---

### Phase 7 — Pull request

**Who:** AI Agent opens, Project Owner reviews and merges

**Steps:**
1. AI Agent opens a PR: base `main`, title is a clear human-readable summary
2. PR description contains `Closes #N` (where N is the Issue number) and
   links to the three artifact files. The `Closes #N` keyword automatically
   links the PR to the Issue in GitHub's Development sidebar and will close
   the Issue when the PR is merged
3. All CI checks must pass: tests, lint, secrets scan
4. Project Owner reviews: code diff, documentation changes, changelog entry
5. Project Owner performs Squash and merge
6. Feature branch deleted automatically
7. AI Agent updates the Issue body: replace all artifact links pointing to
   the feature branch with links pointing to `main`
8. AI Agent updates phase label to `phase: merged`

**Gate:** Issue phase label is `phase: merged` and all artifact links in the
Issue body point to `main`, PR merged to `main`, all CI jobs green.

---

## Release workflow

### Release chore Issue

When the Project Owner decides a set of merged features is ready to be released, they
create a release chore Issue:

**Title:** `Release vX.Y.Z`
**Label:** `chore`
**Milestone:** the milestone being released

The Issue body is a checklist:

```markdown
## Release vX.Y.Z

- [ ] All milestone Issues are closed and merged to `main`
 [ ] `CHANGELOG.md` updated: `UPCOMING` renamed to `vX.Y.Z — YYYY-MM-DD`,
      new empty `UPCOMING` added above it by AI Agent
- [ ] Release prep PR created by AI Agent
- [ ] Release prep PR reviewed and merged by Project Owner
- [ ] Release tag pushed by Project Owner:
      `git tag vX.Y.Z && git push origin vX.Y.Z`
- [ ] Automated release workflow completed: tests → build → GitHub Release created
- [ ] Milestone closed by Project Owner
```

The AI Agent works through the checklist items it owns, checking them off
as each is completed. The Project Owner handles the PR merge and tag push.

### Release preparation steps

1. AI Agent verifies all Issues in the milestone are closed and merged
2. AI Agent creates a release prep branch: `chore/release-vX.Y.Z`
3. In `CHANGELOG.md`:
   - Rename `## UPCOMING` to `## vX.Y.Z — YYYY-MM-DD`
   - Add a new empty `## UPCOMING` section above it
4. AI Agent opens a PR titled `chore: release vX.Y.Z`, with the full
   changelog section for this release included in the PR body
5. Project Owner reviews and merges the PR
6. Project Owner pushes the release tag:
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
7. Automated release workflow runs: tests → build → GitHub Release created
8. AI Agent updates the phase label of all Issues in the milestone from
   `phase: merged` to `phase: released`
9. Project Owner closes the milestone

---

## CHANGELOG.md format

```markdown
# Changelog

## UPCOMING

- Brief human-readable description of each merged feature/fix since last release
- One line per item, written from the user's perspective

## v0.4.0 — 2026-04-20

- Added AVIF and HEIC as supported input formats for the jpegify command
- Fixed timeout handling in rawtherapee command for large files

## v0.3.6 — 2026-03-15

- ...
```

Each UPCOMING entry is added by the AI Agent during the documentation sweep
(Phase 6). It must be one line, written from the user's perspective, not
the implementation perspective.

Good: `Added AVIF and HEIC as supported input formats for the jpegify command`
Bad: `Refactored ImageMagick delegate resolution to support libheif codec`

---

## External Issue intake

### Human-proposed bug or feature

1. Project Owner triages as normal (Phase 1)
2. If accepted: the external Issue body becomes an *input* to Phase 2, not
   the spec itself — produce `spec.md` from it as normal
3. If rejected: close with a brief explanation referencing the personal
   project policy in `CONTRIBUTING.md`

### Private security vulnerability

1. Project Owner assesses severity privately
2. If valid: create a fix branch, follow the standard workflow but keep the
   Issue private until the fix is released
3. After release: optionally publish a public security advisory
4. If invalid: close the advisory with explanation

---

## Project-wide context documents

These documents are persistent inputs for every AI Agent session, regardless
of which feature is being worked on. They must be kept up to date as part of
the documentation sweep in Phase 6.

| Document | Purpose |
|---|---|
| `docs/architecture.md` | Overall structure, module responsibilities, key patterns |
| `docs/conventions.md` | Coding conventions, patterns used consistently in the codebase |
| `docs/SDLC.md` | This document — the development workflow itself |

These documents are produced once (by an AI Agent reading the full codebase)
before AI-assisted development begins, and updated incrementally thereafter.
