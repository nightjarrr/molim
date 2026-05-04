# molim

A personal Linux CLI that wraps RawTherapee, ImageMagick, and FFmpeg behind a single consistent interface for batch file processing. Linux only. External PRs are not accepted.

## Package layout

```
src/molim/
  __init__.py       entry point — main()
  cli.py            CLI setup, command registration
  commands.py       Command base class (template method pattern)
  processing.py     File matching, skipping, output naming, and post-processing strategies
  config.py         TOML config loading (default: ~/.config/molim/config.toml)
  stats.py          Timing and size statistics
  check.py          Guard/assertion functions
  show.py           Rich-based terminal output
  shell.py          Shell subprocess execution via sh library
  rename.py         SuffixCommand
  video.py          VideoFfmpegCommand (FFmpeg)
  images/
    imagemagick.py  ImageMagickMixin
    jpegify.py      JpegifyCommand
    rawtherapee.py  RawTherapeeCommand, RawTherapeeHQCommand
    resize.py       ResizeCommand

tests/              integration tests
docs/               project documentation
```

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

Tests are real integration tests that invoke the actual CLI tools. Do not mock RawTherapee, ImageMagick, or FFmpeg. The tools must be installed and available on PATH for the test suite to pass.

## Branching

Branch names follow the pattern `{type}/{issue-id}-{slug}`.

Examples: `feature/42-avif-support`, `chore/37-add-claude-md`, `fix/51-timeout-handling`.

## Ongoing initiatives

Two parallel long-term efforts are underway, currently in early stages:

- **Agentic SDLC** — a Claude Code-driven development lifecycle for this project. Design is in `docs/AGENTIC-SDLC.md` (written for the human project owner; not agent runtime context).
- **Isolated container runtime** — a hardened, ephemeral Docker environment for Claude Code sessions. Design and current state are in `docs/CLAUDE-DEV-ENVIRONMENT.md` and `docs/CURRENT-STATE.md`.

The isolated container is the primary intended runtime for Claude Code sessions, but the project can be set up and developed in other environments.
