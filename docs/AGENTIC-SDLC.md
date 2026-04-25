# Agentic SDLC

## Purpose and audience

This document defines the conceptual design of an AI-first agentic Software
Development Lifecycle for a Github-hosted project. It describes:

- The roles in the system (human and AI agents)
- The orchestration pattern that connects them
- The permissions and capabilities each role needs
- The skills (reusable capabilities) the AI agents depend on
- The end-to-end workflow for delivering features and releases

**Audience: human Project Owner only.**

This document is read or authored by human at project setup time when configuring the agentic system for a
new project, and when the design of the system itself is being modified. It is
**not** designed to be part of any AI agent's runtime context. Concrete agent instructions and
skill definitions should be  derived artifacts, generated from this design at setup
time and adapted to the specific agentic platform in use (Claude Code, OpenAI
Agents SDK, or others). The vendor-agnostic concepts in this document should be
translated into vendor-specific primitives during that generation step.

---

## Roles

### Project Owner (human)

- Defines requirements and priorities
- Reviews and approves all artifacts at each phase gate
- Makes architectural decisions
- Reviews and merges PRs
- Controls release versioning and pushes release tags
- Single point of contact between the human and the agentic system

### Project Manager (AI agent / orchestrator)

- The only orchestrator agent in the system; the only role that can dispatch
  subagents
- Owns interpretation and execution of the SDLC; reads and applies the workflow
  defined in this document
- Maintains feature-level state by reading GitHub Issues and the repository
- Dispatches Associate Architect or Coder for individual steps within phases
- Acts as a transparent relay between subagents and the Project Owner during
  collaborative work
- Handles all GitHub state updates: phase labels, comments, links, PR creation
- Surfaces phase gate questions to the Project Owner and records approvals

### Associate Architect (AI agent / architect subagent)

- Performs creative, decision-heavy work: drafting specifications, technical
  designs, implementation plans, and project-wide documentation updates
- Step-scoped: invoked by PM for one specific step within a phase, terminates
  on completion
- Communicates with the Project Owner during its work via PM relay
- Produces artifact documents that fully capture decisions and rationale,
  enabling later phases to operate without access to prior session context
- Never writes code on their own, only generates artifacts for the coding phase

### Coder (AI agent / coding subagent)

- Performs implementation: writing code, writing tests, running quality gates
- Step-scoped: invoked by PM for Phase 5 implementation steps
- Only role with shell execution capability
- Communicates with the Project Owner during its work via PM relay

---

## Architecture

### Orchestrator/subagent pattern

The system uses the orchestrator/subagent pattern with human-in-the-loop gates.
Project Manager is the sole orchestrator. Associate Architect and Coder are
subagents dispatched by PM for individual steps.

Subagents do not dispatch other subagents. All inter-role communication flows
through PM.

### Subagent delegation

When PM delegates a step to AA or Coder, it constructs a self-contained task description as the subagent's initial input. This task description includes all context the subagent needs to perform its step independently:
- The originating Issue ID, title, type, and current phase
- The relevant Issue body content and any pertinent comments
- Paths to all prior artifacts produced for this Issue (spec, tech-design, impl-plan, as applicable)
- Paths to relevant project-wide context documents (`architecture.md`,
  `conventions.md`)
- The specific deliverable expected from this step
- Any constraints or decisions surfaced earlier in the workflow that bound the subagent's work

The subagent operates from this self-contained input and does not require access to PM's session history or to the Project Owner's prior conversation with PM. This is what enables phase-scoped subagent sessions and stateless subagent execution.

### Session model

| Role | Session scope | Lifetime |
|---|---|---|
| Project Manager | Feature or release | One PM session per feature, from triaged till merged; release session covers the full release workflow across all upcoming features |
| Associate Architect | Single step | Duration of one delegated step within a phase |
| Coder | Single step | Duration of one delegated step within Phase 5 |

PM sessions begin when the Project Owner instructs PM to work on a feature
or initiate a release, and ends when the current feature gets merged into `main` or is put on pause by Project Owner. State persists between sessions through GitHub Issues and the
repository — the world is stateful, agents are stateless.

Associate Architect does not preserve context of design elaboration with the human across steps and artifacts in phases it is involved into (2, 3, 4, 6). All necessary context — including decision rationale and rejected
alternatives — must be captured explicitly in the artifacts AA produces, so
that subsequent phases can operate on those artifacts alone.

### Communication

- Project Owner communicates with the system through PM exclusively
- Project Owner provides intent (e.g. "proceed with #42"); PM derives the current phase and next action from GitHub Issue state and codebase state. PM always validates Issue and codebase consistency before acting using "Validate Issue" skill. When inconsistencies or missing required state are detected, PM follows the Issue Validation Failure Remediation protocol
- Phase gate approvals are explicit chat exchanges: PM asks for approval, Project Owner
  confirms, PM records the approval as an Issue comment and updates the phase
  label to the next phase
- PM does not automatically advance to proceed work on the next phase after approval; explicitly asks whether to proceed working on the next phase, allowing the Project Owner to pause feature implementation
- When PM relays for a subagent, the active subagent is identified to the
  Project Owner (e.g. "Coder via PM" indicator)
- When acting as a relay between Project Owner and subagent, PM does not interpret or filter the relayed conversation; PM is a transparent pipe during these exchanges, acting only on completion signal and summary of subagent execution from subagent to take over the conversation back

### Escalation

Failures and uncertainty are categorized into four types, each with a defined
escalation path:

| Type | Description | Handling |
|---|---|---|
| 1 — Transient | Technical/infrastructure failures (API timeouts, network) | Role retries internally; escalates only if internal retries and workarounds exhausted |
| 2 — Quality | Failure within role competence (tests fail, output rejected) | Configurable retry threshold per role, then escalate; thresholds set and evolved in agent role instructions, not designed speculatively in this document |
| 3 — Ambiguity | Scope or decision outside role authority | Always escalate to human; encourage proactive early review rather than assumption |
| 4 — Confidence | Work done but uncertainty surfaced | Always surface as information, encourage proactive disclosure and review from human |

Content roles (AA, Coder) escalate to the Project Owner via PM relay. PM
escalates to the Project Owner directly when its own operations encounter
issues. Skills (non-agent capabilities) surface failures to their invoking
agent.

---

## Permission model

Permissions are described in vendor-agnostic manner that map to
specific platform primitives when agent definition is generated.

### Permission categories

| Permission | Covers |
|---|---|
| `fs:read` | Read files from the Git repository checkout on the local filesystem. Includes standard agentic tools usage for codebase reading (Grep, Glob, etc) |
| `fs:write` | Create or modify files on the local filesystem location of the Git repository checkout |
| `git:read` | Read git history, branches, tags, status. Includes Git CLI interface usage for read-only commands |
| `git:write` | Create branches, commit, push. Includes Git CLI interface usage |
| `github:read` | Read Issues, PRs, labels, milestones, CI status via API or Github MCP tool |
| `github:write` | Create/update Issues, PRs, labels, comments, links via API or Github MCP tool |
| `shell:exec` | Execute shell commands (test runners, linters, build tools). The command list is not restructed at conceptual document level but should be restructed at specific agent permission definition |
| `private:memory` | Read/write to a role-private persistent storage. Conceptual design does not make assumptions whether agent memory is project-level, user-level or other but suggests project-level memory (part of Git repository) to be considered as a default |

**IMPORTANT**: The `fs:read` category covers code-reading tools (file reading, content search,
glob matching) and is distinct from `shell:exec` which covers arbitrary command
execution. Implementations should preserve this distinction even when the
underlying mechanism is the same shell.

### Permissions per role

| Permission | PM | AA | Coder |
|---|---|---|---|
| `fs:read` | ✅ | ✅ | ✅ |
| `fs:write` | ❌ | ✅ | ✅ |
| `git:read` | ✅ | ✅ | ✅ |
| `git:write` | ❌ | ✅ | ✅ |
| `github:read` | ✅ | ✅ | ❌ |
| `github:write` | ✅ | ❌ | ❌ |
| `shell:exec` | ❌ | ❌ | ✅ |
| `private:memory` | ✅ | ✅ | ✅ |

Notes:
- PM has no filesystem write or shell access. All file modifications happen through delegated AA or Coder invocations, or through skills that encapsulate write operations (e.g. Cut Release).
- PM is the exclusive holder of `github:write`. All Issue updates, label changes, PR operations, and CI status writes go through PM.
- AA has full `github:read` access to support its information-gathering responsibilities. To produce well-informed specs, technical designs, and implementation plans, AA needs the autonomy to fetch context from any Issue, PR, comment, or related artifact it judges relevant.
- Coder has no GitHub API access. Coder's responsibility ends at "local quality gates pass, branch pushed." PM independently verifies CI status on the pushed branch before reporting phase completion to the Project Owner.
- `shell:exec` is Coder-exclusive. This is the highest-risk permission and warrants the tightest scoping in implementations (sandboxed environment, no network access unless required by the test suite).

---

## Skills

Skills are reusable capabilities that encapsulate well-scoped operations.
Agents invoke skills; skills do not invoke agents. Each skill defines its inputs, outputs, permission requirements, and which agents may invoke it.

### Skill catalog

#### Validate Issue

- **Purpose:** Verify that an Issue's GitHub state is consistent with its current phase label and that all expected artifacts exist on the correct branch
- **Inputs:** Issue ID
- **Outputs:** Structured pass/fail report, listing specific inconsistencies if found
- **Permissions required:** `github:read`, `git:read`, `fs:read`
- **Invoked by:** PM, at every phase transition and as the initial step of every "Work on #XYZ" request by Project Owner

#### Validate Release Readiness

- **Purpose:** Verify that all Issues with `phase: merged` are present in `main`, no Issues are stranded mid-phase, and the CHANGELOG UPCOMING section is non-empty and correctly references all issues with `phase: merged`label. Ensures that the release scope across all tracking channels is consistent and ready to be released 
- **Inputs:** None (operates on current state of repository)
- **Outputs:** Structured readiness report with list of merged-but-unreleased Issues and any inconsistencies if identified
- **Permissions required:** `github:read`, `git:read`, `fs:read`
- **Invoked by:** PM, at the start of a release session

#### Pull Request

- **Purpose:** Construct and open a PR with the correct format (Closes #N for feature PRs, changelog body for release PRs, artifact links), then verify CI status for PR run before reporting completion
- **Inputs:** Branch name, target branch, associated Issue ID, description content
- **Outputs:** PR number, CI status report
- **Permissions required:** `github:write`, `github:read`
- **Invoked by:** PM, in Phase 7 and the release workflow

#### Add Changelog Entry

- **Purpose:** Add a new entry to the UPCOMING section of `CHANGELOG.md`, with the originating Issue ID appended at the end of the line for traceability
- **Inputs:** Issue ID, entry text
- **Outputs:** Confirmation of update, resulting CHANGELOG content (UPCOMING section)
- **Permissions required:** `fs:write`
- **Invoked by:** AA, in Phase 6 documentation update

The skill writes only to `CHANGELOG.md`. The invoking agent (AA) handles the commit as part of its broader documentation update work.

#### Quality Gates

- **Purpose:** Run all project quality checks (tests, format, lint) and produce a unified pass/fail report
- **Inputs:** None (operates on current working directory of Git branch checkout)
- **Outputs:** Structured pass/fail report with per-check results and failure details
- **Permissions required:** `shell:exec`, `fs:read`, `fs:write`
- **Invoked by:** Coder, in Phase 5

`fs:write` access is required for formatting and linting tools to modify codebase and for tests to store any output artifacts (e.g. coverage report)

#### Cut Release

- **Purpose:** Perform all git-side preparation for a release: create the release prep branch, rename the UPCOMING section in `CHANGELOG.md` to the release version with date, add a new empty UPCOMING section above it, commit, and push
- **Inputs:** Version (e.g. `v0.4.0`), date
- **Outputs:** Branch name, commit SHA, confirmation of push
- **Permissions required:** `fs:write`, `git:write`
- **Invoked by:** PM, in the release workflow

The skill owns the full atomic operation. The invoking agent (PM) does not need `git:write` — all git operations are encapsulated within the skill.

### Project Owner helper skills

The following skills are part of the PM's capability set and execute within PM sessions, but they are not invoked by PM autonomously as part of workflow execution. They are made available for the Project Owner to invoke manually through their conversation with PM, supporting the Project Owner in operating the system without requiring constant switching between all involved systems (GitHub Web UI, IDE or Git CLI, AI Coding Agent interface).

#### New Issue

- **Purpose:** Create a new Issue in the correct initial state with proper
  labels and phase
- **Inputs:** Type label (`feature`, `bug`, `chore`, `docs`), one-line description, optional details
- **Outputs:** Created Issue ID and link
- **Permissions required:** `github:write`
- **Invoked by:** Project Owner via PM session (manual invocation only, never autonomous)

Produces a new issue in `phase:triage` state.

#### Upcoming Release

- **Purpose:** Show the Project Owner what would be included in the next release, supporting the release/not-release decision
- **Inputs:** None
- **Outputs:** List of merged PRs since the last release tag, current UPCOMING section of `CHANGELOG.md`, report from "Validate Release Readiness" skill
- **Permissions required:** `github:read`, `git:read`, `fs:read`
- **Invoked by:** Project Owner via PM session (manual invocation only, never autonomous)

#### Current Work

- **Purpose:** Show the Project Owner the status of all active (i.e., triaged, non-merged) features in the backlog
- **Inputs:** None
- **Outputs:** List of open Issues with their phase labels, grouped by phase
- **Permissions required:** `github:read`
- **Invoked by:** Project Owner via PM session (manual invocation only, never autonomous)

---

## Issue validation failure remediation

The `Validate Issue` skill (or `Validate Release Readiness` skill for release sessions) produces a structured report of inconsistencies between an Issue's expected and actual state. PM consumes this report and applies the following remediation protocol whenever inconsistencies are reported:

- PM reports the findings to the Project Owner clearly, listing each specific inconsistency
- PM analyzes the findings and proposes specific remediation when fixes are identifiable (e.g. "Issue lacks a phase label — should I apply   `phase: triage` and proceed with interactive triage?")
- PM applies fixes only after explicit Project Owner approval
- PM never auto-applies fixes silently, even when remediation seems obvious
- If the inconsistency cannot be remediated by PM (e.g. requires Project Owner judgment on Issue scope or content), PM surfaces the situation and awaits Project Owner direction before any further action

This protocol applies at every point where validation runs — session start, phase entry, and any explicit revalidation triggered by the Project Owner. GitHub Issue state is external to the agentic system and may be modified by external actors at any time, so revalidation can detect drift mid-session.

---

## Repository structure

```
docs/
├── architecture.md           # Persistent project-wide architecture reference
├── conventions.md            # Coding conventions and patterns
├── AGENTIC-SDLC.md           # This document — conceptual SDLC design (human audience)
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

GitHub Issues are the tracking and planning layer. Substantive content lives in the repository — Issues link to it.

### Type labels

| Label | Used for |
|---|---|
| `feature` | New functionality |
| `bug` | Defect fixes |
| `chore` | Non-functional work: CI, dependencies, configuration, releases |
| `docs` | Documentation-only changes |

### Phase labels

Phase labels track the current state of an Issue through the development workflow. PM reads the phase label at the start of every session and uses it
to determine current and next steps within the phase, or identify inconsistent state of the issue and escalate it to Project Owner.

| Label | Meaning |
|---|---|
| `phase: triage` | Newly created, awaiting triage by Project Owner or in process of triage |
| `phase: spec` | Spec in progress or awaiting acceptance |
| `phase: tech-design` | Tech design in progress or awaiting acceptance |
| `phase: impl-plan` | Implementation plan in progress or awaiting acceptance |
| `phase: impl-coding` | Coding in progress; ends with code committed, pushed, and CI green on feature branch |
| `phase: impl-docs` | Documentation update in progress; ends with docs committed, pushed, and CI green on feature branch |
| `phase: impl-done` | Implementation and documentation complete, PR ready to be opened or open |
| `phase: merged` | Merged to `main`, pending release |
| `phase: released` | Included in a published release |

Only one phase label is active at a time. PM updates the phase label as each phase completes and the Project Owner approves the gate.

For `docs`-type Issues, the labels `phase: tech-design`, `phase: impl-plan`, `phase: impl-coding`, and `phase: impl-docs` are not used — Phase 2 transitions directly to `phase: impl-done` on Project Owner approval, then through `phase: merged` and release workflow as usual.

### Release tracking

Releases are not tracked through GitHub Milestones. The release model uses multiple complementary mechanisms:

- **Git tag** — authoritative release boundary; what's in `main` at the moment of tagging defines the release content
- **`CHANGELOG.md`** — curated user-facing traceability index; every entry includes the originating Issue ID, making it the human-readable index for "which release contained Issue #XYZ?"
- **GitHub Release auto-generated notes** — exhaustive list of merged PRs for the release; serves as the implementation-level changelog
- **Phase labels** — `phase: merged` identifies Issues ready for the next release; `phase: released` marks them after the release is cut

Backward traceability from a released Issue to its release version is performed by searching `CHANGELOG.md` for the Issue ID.

### Issue ↔ PR ↔ branch linking

GitHub provides first-class linking between Issues, PRs, and branches. PM uses these mechanisms throughout the workflow.

**Branch → Issue link**
When a feature branch is created, PM links the branch to the Issue via the GitHub API. The branch appears in the Issue's Development sidebar.

**PR → Issue link (closing keyword)**
When PM opens a PR, the description includes `Closes #N` where N is the Issue
number. This automatically:
- Links the PR to the Issue in the Development sidebar of both
- Closes the Issue when the PR is merged into `main`
- Creates a cross-reference event in the Issue timeline

**Branch naming convention role**
The `{issue-id}-{slug}` pattern in branch names and `docs/` folder names provides human readability and a back-reference from the folder to the Issue. It is documentation, not the primary linking mechanism — that is handled by GitHub's Development panel and closing keywords.

---

## Feature workflow

The feature workflow is composed of seven phases. PM owns all phases. Within each phase, individual steps are either executed by PM directly or delegated to AA or Coder for execution.

For Issues with the `docs` type label, the workflow is streamlined: only Phases 1, 2, and 7 are run, with Phase 2 covering all required documentation work. See the variation note in Phase 2.

The columns in each phase table are:
- **Step** — the action being taken
- **Executor** — who performs it (Project Owner, PM, AA, or Coder)
- **Skills** — skills invoked during the step

Every phase begins with a Validate Issue step. If Validate Issue reports
inconsistencies, PM follows the Issue Validation Failure Remediation
protocol before proceeding with the rest of the phase.

### Phase 1 — Triage

**Trigger:** new Issue created (by Project Owner manually, by  Project Owner using New Issue skill, externally, or via security report)

| Step | Executor | Skills |
|---|---|---|
| If invoked on a non-labelled, non-triaged Issue, offer to drive interactive triage with the Project Owner | PM | Validate Issue |
| Assign type label if missing (PM applies on Project Owner's instruction during interactive triage) | Project Owner via PM | — |
| Assign `phase:triage` label if missing (PM applies on Project Owner's instruction during interactive triage) | Project Owner via PM | — |
| Review the Issue | Project Owner | — |
| For external Issues: assess and accept or close with explanation | Project Owner | — |
| For private security vulnerabilities: follow security workflow before public exposure | Project Owner | — |
| Set phase label to `phase: spec` | PM | — |

**Gate:** Issue has a type label and `phase: spec` label before Phase 2 begins.


### Phase 2 — Functional specification

**Output:** `docs/{issue-id}-{slug}/spec.md`

**Contents of spec.md:**
- Problem statement / motivation
- Functional requirements (from a user perspective)
- Out of scope (explicit exclusions)
- Acceptance criteria and verification scenarios (from a user perspective)
- Impact on existing functionality
- Alternatives considered and rejected
- Decision log from elaboration with Project Owner

| Step | Executor | Skills |
|---|---|---|
| Read Issue context, validate state | PM | Validate Issue |
| Create feature branch and link to Issue | AA (delegated by PM) | — |
| Draft `spec.md`, iterate with Project Owner | AA (delegated by PM) | — |
| Commit `spec.md` to feature branch, push feature branch | AA (delegated by PM) | — |
| Update Issue body with link to `spec.md` in the feature branch | PM | — |
| On Project Owner approval, set phase label to `phase: tech-design` | PM | — |

**Gate:** Project Owner explicitly accepts the spec.

**Variation for `docs`-type Issues:** for Issues with the `docs` type label, Phase 2 covers all the work — Phases 3 through 6 are skipped, and the workflow proceeds directly to Phase 7. In this case, AA produces the documentation content itself rather than a fixed spec.md, in the form appropriate to the requested deliverable (a new doc, an edit to an existing doc, or both).
No CHANGELOG entry is created — documentation changes are not user-facing software changes and are not included in the curated CHANGELOG. They appear in the GitHub auto-generated release notes via the merged PR list.
On Project Owner approval, PM sets the phase label directly to `phase: impl-done` and the workflow proceeds to Phase 7.

### Phase 3 — Technical design

**Output:** `docs/{issue-id}-{slug}/tech-design.md`

**Contents of tech-design.md:**
- Data model changes (if any)
- Key design decisions and rationale
- Applied design patterns and principles of good code-level design
- Non-functional requirements (performance, security)
- Identified points of extensilbity and configurability parameters
- Affected modules and files
- Test cases and scenarios
- Dependencies or prerequisites introduced
- Impact on existing functionality
- Alternatives considered and rejected
- Decision log from elaboration with Project Owner

| Step | Executor | Skills |
|---|---|---|
| Validate Issue state | PM | Validate Issue |
| Read `spec.md`, `architecture.md`, identified relevant source files | AA (delegated by PM) | — |
| Draft `tech-design.md`, iterate with Project Owner | AA (delegated by PM) | — |
| Commit `tech-design.md` to feature branch, push feature branch | AA (delegated by PM) | — |
| Update Issue body with link to `tech-design.md` in the feature branch | PM | — |
| On Project Owner approval, set phase label to `phase: impl-plan` | PM | — |

**Gate:** Project Owner explicitly accepts the tech design.

### Phase 4 — Implementation plan

**Output:** `docs/{issue-id}-{slug}/impl-plan.md`

**Contents of impl-plan.md:**
- Ordered list of implementation steps
- For each step: files to create/modify/remove, classes/functions to add/change/remove
- Test coverage plan: what new tests are required
- Estimated risk areas or complexity flags

| Step | Executor | Skills |
|---|---|---|
| Validate Issue state | PM | Validate Issue |
| Read `spec.md` and `tech-design.md`, relevant source files listed in `tech-design.md` | AA (delegated by PM) | — |
| Draft `impl-plan.md`, iterate with Project Owner | AA (delegated by PM) | — |
| Commit `impl-plan.md` to feature branch, push feature branch | AA (delegated by PM) | — |
| Update Issue body with link to `impl-plan.md` in the feature branch | PM | — |
| On Project Owner approval, set phase label to `phase: impl-coding` | PM | — |

**Gate:** Project Owner explicitly accepts the implementation plan.

### Phase 5 — Implementation (Coding)

| Step | Executor | Skills |
|---|---|---|
| Validate Issue state | PM | Validate Issue |
| Implement code changes per `impl-plan.md`, iterate with Project Owner on implementation questions | Coder (delegated by PM) | — |
| Write new tests per the test coverage plan, ensure they pass, iterate with Project Owner on implementation questions | Coder (delegated by PM) | — |
| Run all quality gates locally | Coder (delegated by PM) | Quality Gates |
| Flag deviations from impl plan to Project Owner via PM relay | Coder | — |
| Commit code changes to feature branch, push feature branch | Coder (delegated by PM) | — |
| Monitor CI job on feature branch to completion | PM | — |
| On green CI and Project Owner approval, set phase label to `phase: impl-docs` | PM | — |

**Gate:** all tests green, all quality gates passing locally and in CI on feature branch, all deviations from the impl plan resolved or explicitly accepted by Project Owner.

### Phase 6 — Implementation (Documentation update)

| Step | Executor | Skills |
|---|---|---|
| Validate Issue state | PM | Validate Issue |
| Update `architecture.md` if structural changes occurred | AA (delegated by PM) | — |
| Update `README.md` if requirements, commands, or install instructions changed | AA (delegated by PM) | — |
| Update `conventions.md` if new patterns were introduced | AA (delegated by PM) | — |
| Update other affected project-wide docs | AA (delegated by PM) | — |
| Add UPCOMING entry for the feature | AA (delegated by PM) | Add Changelog Entry |
| Commit documentation updates to feature branch, push feature branch | AA (delegated by PM) | — |
| Monitor CI job on feature branch to completion | PM | — |
| On green CI and Project Owner approval of documentation changes, set phase label to `phase: impl-done` | PM | — |

**Gate:** Project Owner accepts all documentation changes, docs committed to feature branch, CI green on feature branch.

### Phase 7 — Pull request

| Step | Executor | Skills |
|---|---|---|
| Validate Issue state | PM | Validate Issue |
| Create PR with `Closes #N`, artifact links, description from feature branch | PM | Pull Request |
| Verify CI checks pass on created PR | PM | Pull Request |
| Review code, documentation, changelog entry once again | Project Owner | — |
| Squash and merge | Project Owner | — |
| Update artifact links (spec, tech-design, impl-plan) in Issue body to point to `main` | PM | — |
| Set phase label to `phase: merged` | PM | — |

**Gate:** PR merged, issue phase label is `phase: merged` and all artifact links in the
Issue body point to `main`.

---

## Release workflow

A release aggregates multiple already-merged Issues into a published version.
The release workflow runs as a separate PM session triggered by the creation
of a release chore Issue.

### Release chore Issue

**Trigger:** Project Owner decides a set of merged features is ready to
release.

**Title:** `Release vX.Y.Z`
**Type label:** `chore`

The Issue body is a checklist tracking the release steps. PM works through the
checklist and updates it as steps complete. Project Owner handles the final
PR merge and tag push.

### Release workflow steps

| Step | Executor | Skills |
|---|---|---|
| Validate that all Issues with `phase: merged` are reflected in `main` | PM | Validate Release Readiness |
| Create release prep branch `chore/release-vX.Y.Z`, update `CHANGELOG.md`, commit and push | PM | Cut Release |
| Monitor CI job on release prep branch to completion | PM | — |
| Open release prep PR with full changelog section in body | PM | Pull Request |
| Verify CI checks pass on created PR | PM | Pull Request |
| Review and merge release prep PR | Project Owner | — |
| Push release tag `vX.Y.Z` | Project Owner | — |
| Monitor automated release workflow runs (CI build, GitHub Release) | PM | — |
| Bulk-update phase labels of all included Issues from `phase: merged` to `phase: released` | PM | — |
| Close release chore Issue | PM | — |

---

## CHANGELOG.md format

```markdown
# Changelog

## UPCOMING

- Brief human-readable description of each merged feature/fix (#42)
- One line per item, written from the user's perspective (#51)

## v0.4.0 — 2026-04-20

- Added AVIF and HEIC as supported input formats for the jpegify command (#38)
- Fixed timeout handling in rawtherapee command for large files (#39)

## v0.3.6 — 2026-03-15

- ...
```

Each entry is added by AA via the Add Changelog Entry skill during Phase 6.
Entries must:
- Be one line, written from the user's perspective
- Describe the user-facing change, not the implementation
- End with the originating Issue ID `(#N)` for traceability

Good: `Added AVIF and HEIC as supported input formats for the jpegify command (#65)`
Bad: `45 - Refactored ImageMagick delegate resolution to support libheif codec`

---

## External Issue intake

### Human-proposed bug or feature

1. Project Owner triages as normal (Phase 1)
2. If accepted: the external Issue body becomes an *input* to Phase 2, not the spec itself — AA produces `spec.md` from it as normal
3. If rejected: close with a brief explanation referencing the project policy
   in `CONTRIBUTING.md`

### Private security vulnerability

1. Project Owner assesses severity privately
2. If valid: create a fix branch, follow the standard workflow but keep the Issue private until the fix is released
3. After release: optionally publish a public security advisory
4. If invalid: close the advisory with explanation

---

## Project-wide context documents

These documents are persistent inputs that may be referenced by AI agents during their work. They are kept up to date by AA during the documentation update in Phase 6.

| Document | Purpose | Audience |
|---|---|---|
| `docs/architecture.md` | Codebase structure, modules, key patterns | AA |
| `docs/conventions.md` | Coding conventions used consistently in the codebase | AA, Coder |
| `docs/AGENTIC-SDLC.md` | This document — conceptual design of the agentic system | Project Owner only |

The architecture document is read by AA when performing decision-heavy work that requires structural awareness of the codebase. The conventions document is read by both AA and Coder when their delegated work involves writing or modifying code or referencing established patterns. They are produced once (by an AI agent reading the full codebase) before AI-assisted development begins and updated incrementally thereafter.

This document (`AGENTIC-SDLC.md`) is read only by the Project Owner during setup and when the system design itself is being modified. It is not part of any agent's runtime context.