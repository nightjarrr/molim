# Contributing

Thank you for your interest in **molim**.

## Project status

This is a personal project, primarily developed for the author's own use.
**Pull requests from external contributors are not being accepted at this time.**

If **molim** is useful to you, feel free to fork the repository and adapt it to
your own needs — that's what the MIT license is for.

## Reporting issues

Bug reports and feature suggestions are welcome via
[GitHub Issues](https://github.com/nightjarrr/molim/issues). Please be aware
that issues may not be addressed promptly, and feature requests may not be
implemented if they fall outside the author's own use cases.

## For forkers

If you fork **molim** and make improvements you think would be valuable upstream,
you are welcome to open an issue describing what you've done. There is no
guarantee of a response, but genuinely useful contributions may be considered
on a case-by-case basis.

## Development setup

If you are working on your own fork, here is how to get a local development
environment running.

**System requirements (Linux only):**

```bash
sudo apt install --no-install-recommends rawtherapee imagemagick ffmpeg
```

**Python environment:**

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the project and all dependencies (including dev tools)
uv sync --all-extras --dev
```

**Install the pre-commit hooks (once per clone):**

```bash
uv run pre-commit install
```

This installs the git hooks that enforce code style automatically on every
commit. This step must be done once on each machine after cloning.

**Running the tests:**

```bash
uv run pytest
```

All tests must pass before any commit. The test suite runs real CLI commands
over pre-defined test files committed to the repository — no mocking of the
underlying tools.

## Code style

The project uses [Ruff](https://docs.astral.sh/ruff/) for both formatting and
linting. Style is enforced at two levels:

**Locally via pre-commit hooks** — on every `git commit`, Ruff automatically
formats the staged files and checks for lint violations. If any files are
modified by the formatter, the commit is blocked so you can review and
re-commit the changes:

```bash
git add .
git commit -m "your message"   # hooks run automatically
# if files were changed by Ruff, review them, then:
git add .
git commit -m "your message"   # clean commit goes through
```

To run the hooks manually across all files (useful after first setup):

```bash
uv run pre-commit run --all-files
```

**In CI** — the lint job in the CI pipeline runs `ruff format --check` and
`ruff check` in read-only mode on every push and pull request. Any formatting
or lint violation will fail the pipeline, blocking merge.

Ruff configuration is in `pyproject.toml` under `[tool.ruff]`.
