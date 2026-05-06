# molim

A personal Linux CLI that wraps RawTherapee, ImageMagick, and FFmpeg behind a single consistent interface for batch file processing. Linux only. External PRs are not accepted.

**Architecture**: composable CLI — commands inherit from the `Command` base class using the Template Method pattern. Source in `src/molim/`, tests in `tests/`, project docs in `docs/`.

**Dev container** infrastructure in `.devcontainer/`, host helper scripts (e.g., launcher) in `scripts/`

## Working together

This project is developed as a human–AI partnership, the agent and the user are working together, each bringing their unique strengths to the table.

**Discuss before you act. ALWAYS.** Before writing code, creating an implementation plan, or producing any other artifact, discuss your intended approach with the user. Be conversational and exploratory: propose ideas, ask questions, surface tradeoffs and alternatives. DO NOT proceed to action (generating a plan or another document, executing a non-trivial sequence of commands, implementing the plan) before asking the user and obtaining an explicit confirmation they are ready to move forward. A short discussion is cheap; building in the wrong direction is costly.

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

## Issues

All work is tracked in GitHub issues. As a first step of every development you need to understand which issue number is tracking it. Run `printenv ISSUE_ID` to check the environment variable, then confirm with the user. The user can give you a different number.

If there is no issue yet, suggest that the user creates it using /new-issue skill.

After obtaining the issue number, read it using `gh` CLI and extract all useful information from it.

## Branching and dev flow

All development happens in feature branches. Branch names follow the pattern `{type}/{issue-id}-{slug}` — for example: `feature/42-avif-support`, `chore/37-add-claude-md`, `docs/51-timeout-handling`.

**Before modifying any repository files**, check the current branch. If it is `main`, create the feature branch first. Use `gh issue develop {issue-id}` to create the branch and link it to the issue. If you are on a feature branch already, no need to create another one. Ensuring that development will go to a feature branch, not `main`, is the required first step of every plan execution, even when the plan does not list it explicitly.

NEVER commit to `main` directly. NEVER merge PRs — merging is a strictly manual human operation that acts as a gate.

## Ongoing initiatives

Two parallel long-term efforts are underway, currently in early stages:

- **Agentic SDLC** — a Claude Code-driven development lifecycle for this project. Design is in `docs/AGENTIC-SDLC.md` (written for the human; not agent runtime context, unless explicitly asked by the user).
- **Isolated container runtime** — a hardened, ephemeral Docker environment for Claude Code sessions. Design and current state are in `docs/CLAUDE-DEV-ENVIRONMENT.md` and `docs/CURRENT-STATE.md`.

The isolated container is the primary intended runtime for Claude Code sessions, but the project can be set up and developed in other environments as well.
