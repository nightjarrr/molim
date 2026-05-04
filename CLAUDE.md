# molim

A personal Linux CLI that wraps RawTherapee, ImageMagick, and FFmpeg behind a single consistent interface for batch file processing. Linux only. External PRs are not accepted.

**Architecture**: composable CLI — commands inherit from the `Command` base class using the Template Method pattern. Source in `src/molim/`, tests in `tests/`, project docs in `docs/`.

## Working together

This project is developed as a human–AI partnership. You and the user have complementary capabilities — tasks that are trivial for a human may be difficult or impossible for an agent, and vice versa. Recognise this asymmetry rather than working against it.

**Discuss before you build.** Before writing code, creating an implementation plan, or producing any other artifact, discuss your intended approach with the user. Be conversational and exploratory: propose ideas, ask questions, surface tradeoffs and alternatives. Do not proceed to implementation until the user has explicitly confirmed they are happy to move forward. A short discussion is cheap; building in the wrong direction is not.

**Know when to ask.** Some tasks are asymmetrically hard: something that requires the agent to experiment with poorly-documented APIs, iterate through failure modes, and invent increasingly complex workarounds may take a human five seconds in a web UI. Recognise this asymmetry early — before deep investment in an approach. The warning signs are: multiple failed attempts at the same goal, escalating complexity with each retry, or finding yourself considering risky workarounds to bypass the original problem. When you notice any of these, stop. Describe what you are trying to accomplish and what you have tried, and propose to discuss options and tackle it together as partners. That is not a failure — it is good judgement about where each partner's capabilities are best applied.

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

All work is tracked in GitHub issues. As a first step of every development you need to understand which issue number is tracking it. Check if environment variable $ISSUE_ID holds the value, then confirm with the user. The user can give you a different number.

If there is no issue yet, suggest that the user creates it using /new-issue skill.

After obtaining the issue number, read it using `gh` CLI and extract all useful information from it.

## Branching and dev flow

Branch names follow the pattern `{type}/{issue-id}-{slug}`.

Examples: `feature/42-avif-support`, `chore/37-add-claude-md`, `docs/51-timeout-handling`.

All development happens in feature branches. NEVER commit to `main` directly. Create feature branches using `gh issue develop` to link it to the issue.

NEVER merge PRs. This is a strictly manual human operation that acts as a gate.

## Ongoing initiatives

Two parallel long-term efforts are underway, currently in early stages:

- **Agentic SDLC** — a Claude Code-driven development lifecycle for this project. Design is in `docs/AGENTIC-SDLC.md` (written for the human; not agent runtime context).
- **Isolated container runtime** — a hardened, ephemeral Docker environment for Claude Code sessions. Design and current state are in `docs/CLAUDE-DEV-ENVIRONMENT.md` and `docs/CURRENT-STATE.md`.

The isolated container is the primary intended runtime for Claude Code sessions, but the project can be set up and developed in other environments as well.
