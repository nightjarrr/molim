# molim — Architecture

## 1. Overview

molim is a personal Linux CLI for batch file processing. It wraps three external tools —
RawTherapee (`rawtherapee-cli`), ImageMagick (`convert`), and FFmpeg (`ffmpeg`) — behind a
single consistent interface.

The execution model is a single invocation: `molim <command> FOLDER [options]`. Each
invocation selects one command, targets one folder, and processes all matching files in that
folder according to the command's rules.

---

## 2. Design principles

These principles govern every design and implementation decision in molim. New features and
changes must be evaluated against them. Where a principle is applied concretely in the
codebase, the relevant section of this document provides detail.

**Single Responsibility** — each class has one clearly defined responsibility. Modules own
distinct concerns: output naming belongs in `OutputFilePathStrategy`, post-processing belongs
in `PostProcessingStrategy`, user output belongs in `show`. Cross-cutting behaviour is
extracted into mixins or shared modules rather than duplicated or inlined.

**Open/Closed** — behaviour is extended through defined extensibility points, not by
modifying existing code. New processing variants are added by subclassing the appropriate
strategy ABC. New commands are registered in `cli.py` without touching the dispatch
machinery. Existing base classes and templates are not modified to accommodate new cases.

**Composability** — complex behaviour is assembled from small, single-purpose objects.
`Command._execute()` composes a pipeline from independently replaceable strategy instances.
The same strategy types are reused across commands; commands differ by the combination they
assemble, not by internal branching. See **Command framework** and **Strategy families**.

**Inversion of Control / Dependency Injection** — components receive their dependencies via
constructors. There is no DI framework and no service locator. `Command._execute()` is the
composition root: it instantiates all strategies and processors and wires them together.
There are no singletons or shared mutable instances. See **Processing pipeline**.

**Self-contained environment** — after `uv sync --frozen`, the project builds, tests, and
runs with no further setup. The only external prerequisites are the three CLI tools on PATH.
New features must preserve this. Introducing a dependency on a new system tool or library
requires explicit justification. See **Toolchain and development environment**.

**Dry-run universality** — `--dry-run` is a first-class feature, not an afterthought. Every
operation that modifies the filesystem must honour the `dry_run` flag. This is a
non-negotiable constraint on all new `FileProcessor` and `PostProcessingStrategy`
implementations. See **Dry-run mode**.

**Fail fast** — invalid state is detected and reported at the earliest possible point.
External tool availability is verified at processor instantiation, not at first use. Input
validation is applied at every internal API boundary via the `check` module. Errors propagate
to the top-level handler; unexpected failures are not silently swallowed.

---

## 3. Toolchain and development environment

- **Package manager**: `uv` exclusively. No `pip`, no `poetry`, no direct venv activation or
  deactivation. All interactions go through `uv` subcommands. `uv pip` must also be avoided.
- **Running**: `uv run <command>` — e.g. `uv run pytest`, `uv run ruff format .`,
  `uv run molim`. `uv run` resolves the project virtualenv automatically.
- **Dependencies**: `uv sync --frozen` installs the locked set from `uv.lock` (committed).
  `uv add <package>` / `uv add --dev <package>` for adding new dependencies.
- **Building**: `uv build` produces wheel and sdist in `dist/`.
- **Python version**: managed by uv from `.python-version` / `requires-python` in
  `pyproject.toml`. No assumption about system Python.

  The only external prerequisites are the three CLI tools on PATH (`rawtherapee-cli`,
  `convert`, `ffmpeg`). See the **Self-contained environment** principle.

---

## 4. Package layout

Source lives under `src/molim/`. Image-specific functionality is grouped in `src/molim/images/`.

| Module | Responsibility |
|---|---|
| `__init__.py` | Entry point; `main()` calls `cli.run()`; top-level exception handling (exit codes 130 / 1) |
| `cli.py` | Command registry; instantiates all concrete commands; argparse dispatch |
| `commands.py` | `Command` ABC (Template Method); shared CLI arguments; argument converter types |
| `processing.py` | Strategy ABCs and concrete variants for output naming, post-processing, file matching, skipping, and per-file processing; `FolderProcessor` |
| `shell.py` | `ShellCommandFileProcessor`; wraps the `sh` library for external CLI tool invocation |
| `config.py` | TOML config loader; `ConfigReader`; per-command and global section lookup |
| `check.py` | Input validation functions (type, path, range, format checks) |
| `show.py` | All user-facing output via Rich; progress bars, size/time formatting, verbose gating |
| `stats.py` | `FileStats` and `FolderStats` context managers for per-file and summary statistics |
| `video.py` | `VideoFfmpegCommand` and `FfmpegFileProcessor` |
| `rename.py` | `SuffixCommand` and `RenameFileProcessor` (filesystem rename, no shell, pure Python stdlib) |
| `images/__init__.py` | Shared `images` package-wide constants (`JPEG_QUALITY`, `JPEG_PROCESSED_EXTENSION`, etc.) |
| `images/imagemagick.py` | `ImageMagickMixin` and `ImageMagickFileProcessor` |
| `images/jpegify.py` | `JpegifyCommand` — converts PNG / WebP / AVIF / HEIC to JPEG via ImageMagick |
| `images/resize.py` | `ResizeCommand` — resizes JPEG via ImageMagick `-resize` |
| `images/rawtherapee.py` | `RawTherapeeCommand` and `RawTherapeeHQCommand` — batch RAW processing via RawTherapee profiles; `RawTherapeeHQCommand` uses higher quality defaults |

---

## 5. Processing pipeline

Execution nesting from CLI invocation to external tool run:

```
molim <cmd> FOLDER              # __init__.main() → cli.run(sys.argv[1:])
  └─ argparse dispatch           # cli._create_parser() → args.command(args)
       └─ Command._execute()     # loads config, composes strategies
            └─ FolderProcessor.process()        # iterates folder
                 └─ FileProcessor.process()     # per matched, non-skipped file
                      └─ ShellCommandFileProcessor._execute()   # sh.Command(...)
                           └─ rawtherapee-cli / convert / ffmpeg
```

Strategy composition in `Command._execute()`:

1. Resolve and validate `FOLDER` path.
2. Load TOML config (command-specific section).
3. Instantiate `OutputFilePathStrategy` via `_get_output_file_path_strategy(args)`.
4. Instantiate `PostProcessingStrategy` via `_get_post_processing_strategy(folder, args)`.
5. Instantiate `FileProcessor` via `_get_file_processor(args, output_namer, post_processor)`.
6. Instantiate `FileMatchStrategy` via `_get_file_match_strategy(args)`.
7. Instantiate `FileSkipStrategy` via `_get_file_skip_strategy(args)`, then wrap with
   config-driven glob skips from `_get_global_skip_strategy()`.
8. Run `FolderProcessor(folder, matcher, skipper, processor).process(dry_run, show_size)`.
9. Display `FolderStats`.

`Command._execute()` is the composition root (see **IoC/DI**): it instantiates all strategies and processors and wires them into `FolderProcessor`.

---

## 6. Command framework

`Command` in `commands.py` is the abstract base class. It implements the Template Method
pattern: `_execute()` is the fixed template that orchestrates every processing run.
Subclasses implement hook methods; they do not override `_execute()` — this is **Open/Closed** applied to the command pipeline. When overriding is unavoidable, `super()._execute(args)` must be called to augment rather than replace the pipeline. See `conventions.md` for the full override rules.

**Hooks subclasses must implement:**

| Method or property | Returns |
|---|---|
| `name` (property) | CLI subcommand name string |
| `help` (property) | CLI help text string |
| `_add_arguments(parser)` | Adds command-specific argparse arguments |
| `_get_common_arguments_defaults()` | Tuple of defaults / `None` values for the four common slots |
| `_get_output_file_path_strategy(args)` | An `OutputFilePathStrategy` instance |
| `_get_file_processor(args, output_namer, post_processor)` | A `FileProcessor` instance |
| `_get_file_skip_strategy(args)` | A `FileSkipStrategy` instance |

`configure_parser()` calls `_add_arguments()` then `_add_common_arguments()` —
command-specific arguments appear first in help output. `__call__(args)` delegates to
`_execute()`; commands are callable objects registered via `parser.set_defaults(command=self)` and called by `argparse`.

**Registered commands** (instantiated in `cli.run()`):

| Command | Class | Module | External tool |
|---|---|---|---|
| `video` | `VideoFfmpegCommand` | `video.py` | `ffmpeg` |
| `jpegify` | `JpegifyCommand` | `images/jpegify.py` | `convert` (ImageMagick) |
| `resize` | `ResizeCommand` | `images/resize.py` | `convert` (ImageMagick) |
| `rawtherapee` | `RawTherapeeCommand` | `images/rawtherapee.py` | `rawtherapee-cli` |
| `rawtherapee-hq` | `RawTherapeeHQCommand` | `images/rawtherapee.py` | `rawtherapee-cli` |
| `suffix` | `SuffixCommand` | `rename.py` | — (Python stdlib only) |

**Mixin pattern**: `JpegifyCommand` and `ResizeCommand` inherit
`(commands.Command, ImageMagickMixin)`. `ImageMagickMixin` encapsulates all ImageMagick
integration: it adds `--imagemagick-quality` and `--imagemagick-additional` CLI arguments, and
provides the `ImageMagickFileProcessor` that constructs and runs the `convert` invocation.
Because `Command` is listed first in the MRO, Python resolves `Command`'s abstract methods
before the mixin's implementations, so subclasses must explicitly delegate `_add_arguments`
and `_get_file_processor` to `ImageMagickMixin`. See `conventions.md` for the full mixin
delegation pattern.

---

## 7. CLI composability

The CLI uses argparse subparsers: one per command, each with a fully isolated argument
namespace. Adding a new command requires no changes to the dispatch machinery in `cli` —
instantiate the class and pass it to `_create_parser()`. This is **Open/Closed** applied to the CLI.

**Three-tier argument structure:**

- *Always-present* — every command must support unconditionally: `FOLDER` (positional), `--config`,
  `--dry-run`, `--verbose`, `--extension`. Added by `_add_common_arguments()`; cannot be
  suppressed. Commands supply the default for `--extension` via `_get_common_arguments_defaults()`.
- *Optional common slots* — three shared arguments each command opts into or suppresses by
  returning a default value or `None` from `_get_common_arguments_defaults()`:
  - `--greater-than` — minimum file size threshold
  - `--no-skip-processed` — disable already-processed file detection by suffix
  - `--originals` — post-processing disposition (`leave` / `move` / `delete`)
- *Command-specific* — arbitrary additional arguments defined in `_add_arguments()`, scoped
  entirely to that command (e.g. `--codec`, `--profile`, `--imagemagick-quality`).

**Flexibility**: commands compose their own argument surface by choosing which common slots to
expose and adding as many command-specific arguments as needed. Commands with no concept of
originals handling (e.g. `suffix`) suppress that slot by returning `None`; the argument does
not appear in their help text or namespace.

**Constraints**: `_get_common_arguments_defaults()` returns a fixed four-element tuple
`(extension, greater_than, no_skip_processed, originals)`. The first element sets the default
for `--extension` but cannot suppress it — `--extension` is always added regardless of the
value returned. The remaining three act differently: a non-`None` value sets the default and
adds the argument; `None` suppresses it entirely. This mixed behaviour — one always-present
element and three suppressible ones packed into the same tuple — is a design inconsistency.
Adding a new element to the tuple requires updating `_add_common_arguments()`, the method
signature, and every subclass return statement — changes are codebase-wide.

---

## 8. Dry-run mode

Dry-run is a first-class feature present on every command. `--dry-run` is defined in
`Command._add_common_arguments()` and propagated through the entire processing pipeline.

When `dry_run=True`:

- `Command._execute()` passes the flag to `FolderProcessor.process()`.
- `FolderProcessor` passes it to each `FileProcessor.process()` call.
- `ShellCommandFileProcessor` logs the intended command but does not invoke the external
  tool.
- `RenameFileProcessor` logs the intended rename but does not call `Path.rename()`.
- `PostProcessingStrategy` implementations (move, delete) skip their filesystem operations.
- Input validation, output path computation, and stats reporting still run in full — the
  user sees exactly what would happen.

See the **Dry-run universality** principle.

---

## 9. Strategy families

`processing.py` defines six pluggable behaviour families. New variants are added by
subclassing the appropriate ABC — no conditionals in base classes (**Open/Closed**).

| Family ABC | Concrete variants | Controls |
|---|---|---|
| `OutputFilePathStrategy` | `SuffixOutputFilePathStrategy`, `ChangeExtOutputFilePathStrategy`, `FolderOutputFilePathStrategy`, `MultiOutputFilePathStrategy` | How output files are named and where they are placed |
| `PostProcessingStrategy` | `NoopPostProcessingStrategy`, `MoveOriginalPostProcessingStrategy`, `DeleteOriginalPostProcessingStrategy`, `ReplaceOriginalPostProcessignStrategy` | What happens to the original file after processing |
| `FileMatchStrategy` | `AnyFileMatchStrategy`, `ByExtensionFileMatchStrategy` | Which files in a folder are considered for processing |
| `FileSkipStrategy` | `NoFileSkipStrategy`, `BySuffixFileSkipStrategy`, `BySizeFileSkipStrategy`, `GlobFileSkipStrategy`, `MultiFileSkipStrategy` | Which matched files are skipped |
| `FileProcessor` | `ShellCommandFileProcessor` subtypes, `RenameFileProcessor` | How a single file is processed |
| (orchestrator) | `FolderProcessor` | Iterates the folder, applies match / skip / process, aggregates `FolderStats` |

---

## 10. External tool integration

`ShellCommandFileProcessor` in `shell.py` is the bridge between Python and external CLI
tools. It uses the `sh` library.

- **Tool verification**: the constructor calls `sh.Command(command)` and runs
  `_get_verify_args()` at instantiation — fails fast if the tool is missing from PATH
  (**Fail fast**).
- **Argument construction**: `_finalize_args(input_path, output_path)` is abstract; each
  subclass constructs the tool-specific argument list from the input and output file paths.
- **Dry-run**: `process()` logs the intended invocation and skips `_execute()` when
  `dry_run=True`.

Tool-specific processors:

| Processor | Tool | Argument shape |
|---|---|---|
| `FfmpegFileProcessor` | `ffmpeg` | `-y -i <in> -vcodec <codec> -crf <rate> [extra] [-report] <out>` |
| `ImageMagickFileProcessor` | `convert` | `<in> [-quality N] [extra] <out>` |
| `RawTherapeeFileProcessor` | `rawtherapee-cli` | `-o <out> -q -d -Y -p <profile.pp3> -j<quality> -js<subsampling> -c <in>` |

**RawTherapee profile resolution** (first match wins):
1. `--profile-folder` CLI argument
2. `profile-folder` key in config file
3. Default: `~/.config/RawTherapee/profiles`

Profile name: `--profile` CLI argument → config `profile` key → default `molim`.

---

## 11. Configuration

- **File location**: `~/.config/molim/config.toml` (default); overridden per invocation via
  `--config`.
- **Structure**: TOML with a `[global]` section and per-command sections (e.g.
  `[rawtherapee]`).
- **Lookup order**: `ConfigReader.__call__(key)` checks the command-specific section first,
  then `[global]`.
- **Fully opt-in**: no config file, no section, no entry — each is independently optional.
  Processing continues normally at every level of absence. There are no required entries.
  Configuration is additive: commands opt in to reading config values; nothing is compulsory.
  At design time, "should this be configurable in `config.toml`?" is always worth asking —
  there are no technical constraints that push toward adding configurable options, so the
  decision is purely about user value.

---

## 12. Tests

- **Approach**: real integration tests — `rawtherapee-cli`, `convert`, and `ffmpeg` are
  invoked for real. No mocking of external tools.
- **Location**: `tests/` at repo root, alongside `src/`.
- **File naming**: `{module}_test.py` (e.g. `video_test.py`). When a module's tests are
  large enough to split: `{module}_{aspect}_test.py` (e.g. `processing_files_test.py`,
  `processing_folders_test.py`).
- **Shared fixtures and constants**: `tests/common.py`.
- **Static test data**: `tests/data/{module}/` — sample media files and config files needed
  by tests that require real inputs.
- **Temporary filesystem state**: `tmp_path` (function-scoped) and `tmp_path_factory`
  (module-scoped) pytest fixtures. Temp state must be always cleaned up as a teardown step - no matter if the test passes or fails.
- **`monkeypatch`**: permitted only for infrastructure concerns where no real tool exists
  (e.g. stubbing `importlib.metadata.version()` for version detection). Never used to
  substitute external CLI tools.
- **Test categories per class**: input validation, dry-run behavior, core logic.
- **Runner**: pytest with branch coverage (`pytest-cov`); reports uploaded to Codecov in CI.
- **Coverage requirement**: tests are not optional. Every new class or method requires tests.
  Every bug fix requires a regression test that validates the corrected behaviour and catches
  future regressions at the test stage.

---

## 13. Build, release, and distribution

- **Build system**: `hatchling` + `hatch-vcs` (`pyproject.toml`). `uv build` produces a
  wheel and source distribution in `dist/`.
- **Versioning**: derived from git tags via `hatch-vcs` (`source = "vcs"`). A `vX.Y.Z` tag
  on `main` sets the release version. Untagged commits fall back to `0.0.0.dev0`.
- **Entry point**: `molim = "molim:main"` in `[project.scripts]` — the installed package
  provides the `molim` CLI command.
- **Release workflow** (`.github/workflows/release.yml`): triggered by a `v*` tag push.
  Runs the full base CI, then builds the package and creates a GitHub Release with the wheel
  and sdist attached. Release notes are auto-generated by GitHub from merged PRs.
- **Distribution**: GitHub Releases only. molim is a personal tool and is not published to
  PyPI. Users install from a GitHub Release artifact (e.g. `uv tool install` from the wheel
  URL or directly from the repository).

---

## 14. Continuous integration

- **CI workflow** (`.github/workflows/ci.yml`): runs on every push to any branch and every
  pull request. Delegates to `base.yml`.
- **Release workflow** also runs `base.yml` as a prerequisite, so the same checks gate every
  release.
- **Base workflow** (`.github/workflows/base.yml`): three parallel jobs:
  - `run_pytest` — installs system tools (`rawtherapee`, `imagemagick`, `ffmpeg`), runs
    `uv run pytest` with branch coverage; uploads HTML report as a workflow artifact and
    coverage data to Codecov.
  - `lint` — runs `uv run ruff format --check .` and `uv run ruff check .`; no auto-fix,
    fails on violations.
  - `scan_secrets` — full-history `gitleaks` scan on every run.
