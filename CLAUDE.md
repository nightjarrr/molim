# molim

A personal Linux CLI that wraps RawTherapee, ImageMagick, and FFmpeg behind a single consistent interface for batch file processing. Linux only. External PRs are not accepted.

**Architecture**: composable CLI — commands inherit from the `Command` base class using the Template Method pattern. Source in `src/molim/`, tests in `tests/`, project docs in `docs/`.

**Dev container** infrastructure in `.devcontainer/`, host helper scripts (e.g., launcher) in `scripts/`

## Working together

This project is developed as a human–AI partnership, the agent and the user are working together, each bringing their unique strengths to the table.

**Discuss before you act. ALWAYS.** Before writing code, creating an implementation plan, or producing any other artifact, discuss your intended approach with the user. Be conversational and exploratory: propose ideas, ask questions, surface tradeoffs and alternatives. DO NOT proceed to action (generating a plan or another document, executing a non-trivial sequence of commands, implementing the plan) before asking the user and obtaining an explicit confirmation they are ready to move forward. A short discussion is cheap; building in the wrong direction is costly.

**Separate analysis from decision.** When working together through an architecture design, open question or exploring a new idea, stay in analysis mode until the analysis is complete. Surface dimensions, tradeoffs, and implications as they emerge; do not race to a conclusion early. Do not recommend or offer your choice for an option until the full picture is established; a recommendation before the analysis is complete is unlikely to stick when new facts or considerations are discovered. In analysis mode, prioritize broad thinking and search to uncover the unknowns, not the shortcut to a quick answer based on narrow vision. When a new consideration changes the picture, update the holistic analysis but do not issue a new recommendation right away.
 
The transition to decision mode happens when the user says so unprompted, or when the model asks and the user confirms. The right moment to ask is when exploration feels exhausted: the unknowns have been named, the tradeoffs mapped, and the model feels it could offer a well-grounded opinion. When the time of decision comes, form a conclusion once and ground it in the full analysis. Be ready to defend it on the merits; if challenged, engage with the opposing argument on its substance. Update the conclusion if the reasoning warrants it; don't update it just because the pushback is uncomfortable.

**Know when to stop and ask.** You and the user have complementary capabilities — tasks that are trivial for a human may be difficult or impossible for the agent, and vice versa. Because of that, some tasks are asymmetrically hard: something that requires the agent to experiment with poorly-documented APIs, iterate through failure modes, and invent increasingly complex workarounds may take the user five seconds in a web UI inaccessible by the agent. Recognise this asymmetry early — before deep investment into agent-only approach. The warning signs are: multiple failed attempts at the same goal, escalating complexity with each retry, or finding yourself considering risky workarounds to bypass the problem that did not exist originally. When you notice any of these, STOP. Describe to the user what you are trying to accomplish and what you have tried, and propose to discuss options and tackle it together as partners. That is not a failure, it is good judgement about where each partner's capabilities are best applied.

## Dev commands

```bash
uv run pytest                      # run tests (requires rawtherapee, imagemagick, ffmpeg on PATH)
uv run ruff format .               # format
uv run ruff check .                # lint
uv run pre-commit run --all-files  # run all hooks across all files
```

## Code style

Ruff handles formatting and linting. Configuration is in `pyproject.toml` under `[tool.ruff]`. Key settings: line length 128, double quotes, Python 3.12 target.

Pre-commit hooks run ruff on every `git commit`. If the formatter modifies staged files, the commit is blocked — review the changes, re-stage, and commit again.

## Tests

Tests are real integration tests that invoke the actual CLI tools. Do not mock RawTherapee, ImageMagick, or FFmpeg. Required commands on PATH: `rawtherapee-cli`, `convert` (ImageMagick), `ffmpeg`.

Tests are required for new Python code. Each bugfix must be covered by a set of tests to catch any future regressions.

## Proto-SDLC (until full Agentic SDLC implemented)

Every implementation task — regardless of size — follows this workflow from start to finish. Begin at step 1 whenever a new task is introduced. Steps 3–8 form an iteration loop: if Coder's output is not approved, the plan is amended and implementation repeats until the user signs off. Only then does the work proceed to step 9 (open PR).

### 1. Issue identification

Run `printenv ISSUE_ID` to check the issue number, then confirm with the user. The user can provide a different number. If no issue exists yet, use the `/new-issue` skill to create one.

Read the issue body and comments — two calls are needed:

```bash
gh issue view {issue-id}
gh issue view {issue-id} --comments
```

Comments contain the latest state for ongoing work and must be read alongside the issue body.

### 2. Feature branch

Branch names follow the pattern `{type}/{issue-id}-{slug}` — for example: `feature/42-avif-support`, `chore/37-add-claude-md`, `docs/51-timeout-handling`.

**Before modifying any repository files**, check the current branch. If it is `main`, create the feature branch first: `gh issue develop {issue-id}`. If already on a feature branch, no further action needed.

NEVER commit to `main` directly. NEVER merge PRs — merging is a strictly manual human operation that acts as a gate.

### 3. Plan

Enter plan mode. Write an implementation plan with three sections:

**Requirements.** What the issue requires: what must be done, acceptance criteria, and implementation constraints. Self-contained — Coder should be able to implement from this plan without reading the issue or other docs.

**Architecture context.** A filtered view of the parts of the system this change touches: relevant files, classes, and patterns. Proportional to complexity — a trivial change may need a sentence; a cross-cutting change may need a substantial section.

**Work breakdown.** Ordered list of implementation steps. For each step: files to create/modify/remove, classes/functions to add/change/remove. Include test coverage plan and any risk areas.

Iterate with the user in plan mode until the plan is approved.

### 4. Post plan

Post the approved plan as a comment to the issue:

```bash
gh issue comment {issue-id} --body-file {path-to-plan-file}
```

### 5. Implement

Dispatch the `@coder` subagent with: issue id, issue title, issue type, path to the plan file (instruct Coder to treat it as `impl-plan.md`), and any additional context or instructions from the conversation.

### 6. Review

After Coder terminates, surface the verbatim structured final response to the user and ask for review and approval.

### 7. Post outcome

On user approval, post Coder's structured final response as a comment to the issue:

```bash
gh issue comment {issue-id} --body "..."
```

### 8. Iterate

If the user does not approve, amend the plan and repeat from step 3. Once the user approves, proceed to step 9.

### 9. Open PR

Verify all commits are pushed (`git push` if needed — Coder pushes as part of its work, but confirm nothing is outstanding). Then open a pull request:

```bash
gh pr create --title "..." --body "..."
```

## Ongoing initiatives

Two parallel long-term efforts are underway, currently in early stages:

- **Agentic SDLC** — a Claude Code-driven development lifecycle for this project. Design is in `docs/AGENTIC-SDLC.md` (written for the human; not agent runtime context, unless explicitly asked by the user).
- **Isolated container runtime** — a hardened, ephemeral Docker environment for Claude Code sessions. Design and current state are in `docs/CLAUDE-DEV-ENVIRONMENT.md` and `docs/CURRENT-STATE.md`.

The isolated container is the primary intended runtime for Claude Code sessions, but the project can be set up and developed in other environments as well.
