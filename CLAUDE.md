# molim

A personal Linux CLI that wraps RawTherapee, ImageMagick, and FFmpeg behind a single consistent interface for batch file processing. Linux only. External PRs are not accepted.

**Architecture**: composable CLI — commands inherit from the `Command` base class using the Template Method pattern. Source in `src/molim/`, tests in `tests/`, project docs in `docs/`.

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

All work is tracked in Github issues. As a first step of every development you need to understand which issue number is tracking it. Check if environment variable $ISSUE_ID holds the value, then confirm with the user. The user can give you a different number.

If there is no issue yet, suggest that the user creates it using /new-issue skill.

After obtaining the issue number, read it using `gh` CLI and extract all useful information from it.

## Branching and dev flow

Branch names follow the pattern `{type}/{issue-id}-{slug}`.

Examples: `feature/42-avif-support`, `chore/37-add-claude-md`, `docs/51-timeout-handling`.

All development happens in feature branches. NEVER commit to `main` directly. Create feature branches using `gh issue develop` to link it to the issue.

NEVER merge PRs. This is a strictly manual human operation that acts as a gate.

## Ongoing initiatives

Two parallel long-term efforts are underway, currently in early stages:

- **Agentic SDLC** — a Claude Code-driven development lifecycle for this project. Design is in `docs/AGENTIC-SDLC.md` (written for the human project owner; not agent runtime context).
- **Isolated container runtime** — a hardened, ephemeral Docker environment for Claude Code sessions. Design and current state are in `docs/CLAUDE-DEV-ENVIRONMENT.md` and `docs/CURRENT-STATE.md`.

The isolated container is the primary intended runtime for Claude Code sessions, but the project can be set up and developed in other environments as well.
