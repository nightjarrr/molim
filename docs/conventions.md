# Coding Conventions

PEP 8 is the base style. This document lists all points where the codebase intentionally deviates from PEP 8, then covers project-specific conventions that PEP 8 does not address. Apply PEP 8 for anything not listed here.

---

## Scope

These conventions apply to Python source code under `src/molim/` and tests under `tests/`.

`molim` is a Linux-only CLI application. Do not add portability abstractions for unsupported platforms.

---

## PEP 8 deviations

### Line length: 128 characters

Maximum line length is 128 characters (PEP 8: 79). Configured in `pyproject.toml` and enforced by Ruff.

### Private instance attributes: double underscore prefix

Private instance attributes use double underscore (`self.__attr`), not single underscore. Single underscore is a convention-only signal that a fresh reader may not immediately register as "do not touch"; double underscore makes the intent unambiguous at a glance. It also triggers Python name mangling (`_ClassName__attr`), which prevents accidental attribute collision in subclasses as a secondary benefit. Apply consistently to all instance attributes not intended for subclass or external access.

---

## Naming

Ruff is not configured with naming rules (`N` rule set is not enabled). Correct naming is the agent's sole responsibility — no linting safety net exists.

Follow PEP 8 naming:

| Kind | Convention | Example |
|---|---|---|
| Classes | `PascalCase` | `ShellCommandFileProcessor` |
| Functions, methods, variables | `snake_case` | `get_output_path`, `folder_path` |
| Constants | `SCREAMING_SNAKE_CASE` | `VIDEO_FFMPEG_CODEC`, `ANY_MATCH_EXTENSION` |
| Protected methods (overridable by subclasses) | `_single_underscore` | `_add_arguments`, `_execute` |
| Private instance attributes | `__double_underscore` | `self.__config`, `self.__command` |

Use consistent class name suffixes to communicate role and inheritance line:

| Suffix | Used for |
|---|---|
| `*Command` | CLI command implementations |
| `*Strategy` | Strategy pattern implementations |
| `*FileProcessor` | File processor implementations |
| `*Mixin` | Mixin classes |
| `*Error` | Custom exception classes |

---

## Type annotations

Annotate all function and method signatures — parameters and return types. Use Python 3.12 built-in generics (`list[str]`, `tuple[str, int]`). Do not use `typing.List`, `typing.Tuple`, or other deprecated aliases.

Use `pathlib.Path` for all filesystem paths inside application logic. Convert incoming string paths at the boundary; work with `Path` objects throughout.

---

## Module layout

```
src/molim/
├── __init__.py       # Entry point: main()
├── cli.py            # CLI runner and command list
├── commands.py       # Command base class and argument types
├── check.py          # Input validation functions
├── config.py         # Config file reader
├── processing.py     # Strategy classes for file processing
├── shell.py          # Shell execution wrapper
├── show.py           # User-facing output
├── stats.py          # Statistics context managers
└── images/           # Image-specific commands and processors
```

One module per command or functional area. Image-processing commands go under `images/`. New commands get their own module file. When adding new functionality, decide first whether it belongs in an existing cross-cutting module (`check`, `processing`, `shell`, `show`) or in a domain-specific command module — do not let `cli.py` or `commands.py` grow into catch-all implementation files.

---

## Imports

Import grouping follows Ruff/isort: standard library, then third-party packages, then local package imports.

Within the package, use relative imports:

```python
from . import check, commands, processing, show
from .images import jpegify, rawtherapee, resize
```

Import from the module that owns the concept. Avoid broad dependency reach-through.

---

## Adding a command

1. Create a new module in `src/molim/` (or `src/molim/images/` for image commands).
2. Subclass `Command`.
3. Implement all abstract methods (each raises `NotImplementedError` in the base class):
   - `name` → `str` — CLI subcommand name
   - `help` → `str` — help text
   - `_add_arguments(parser)` → adds command-specific argparse arguments; returns parser
   - `_get_common_arguments_defaults()` → returns `(extension, greater_than, no_skip_processed, originals)` tuple; pass `None` for any optional common argument to suppress it
   - `_get_output_file_path_strategy(args)` → returns an `OutputFilePathStrategy`
   - `_get_file_processor(args, output_namer, post_processor)` → returns a `FileProcessor`
   - `_get_file_skip_strategy(args)` → returns a `FileSkipStrategy`
4. Define command defaults as module-level constants named `{COMMAND}_{PARAMETER}` (e.g., `VIDEO_FFMPEG_CODEC`, `JPEG_QUALITY`). Use them in `_get_common_arguments_defaults()` — do not inline literal values.
5. Use kebab-case for all CLI flags: `--dry-run`, `--greater-than`, `--imagemagick-quality`.
6. Register the command in `cli.py` by instantiating it in `_create_parser(...)`.
7. Add tests covering argument parsing, input validation, dry-run behavior, and core logic.
8. Run `uv run pre-commit run --all-files` and `uv run pytest` before committing.

Do not override `_execute` unless there is no other way to achieve the required behaviour. Overriding the template method is a conscious deviation from the established pattern and requires: explicit rationale discussed with and approved by the Project Owner, documentation in the tech design doc for the feature, and a code comment at the override site explaining why the hook methods were insufficient. If overriding is unavoidable, always call `super()._execute(args)` — augment the invocation pipeline, do not replace it.

---

## Design patterns

These patterns are established. Extend them; do not introduce alternatives.

The codebase uses nominal typing rather than duck typing. New implementations must inherit from the established abstract base class for their role — do not create lookalike classes that merely implement the same methods. Abstract methods are defined with `raise NotImplementedError()` rather than `@abc.abstractmethod`; the convention is deliberate and should be followed consistently.

**Template Method** (`commands.py`) — `Command._execute()` orchestrates the processing pipeline. Subclasses implement the hook methods. Do not override `_execute` unless there is no other way to achieve the required behaviour — see the rule in the Adding a command section.

**Strategy** (`processing.py`) — pluggable behaviours for output path naming, post-processing, file matching, and file skipping. Add new variants by subclassing the appropriate abstract base: `OutputFilePathStrategy`, `PostProcessingStrategy`, `FileMatchStrategy`, `FileSkipStrategy`, `FileProcessor`. Before adding conditionals to an existing method, consider whether the new behaviour should instead be a new strategy, a command subclass, or a mixin. Use composition for pipelines: combine behaviours through `Multi*` strategies rather than hard-coding special cases. Keep concerns separate: output naming belongs in `OutputFilePathStrategy`; moving, deleting, or replacing originals belongs in `PostProcessingStrategy`.

**Mixin** — injects shared functionality into classes alongside their primary inheritance line. Use a mixin when multiple command classes need the same cross-cutting capability that does not belong in the `Command` base class. Example: `ImageMagickMixin` provides the complete ImageMagick integration — argument parsing, validation, and the `ImageMagickFileProcessor` that runs `convert` — satisfying both `_add_arguments` and `_get_file_processor` for any command that processes images with ImageMagick. Classes using the mixin are still proper `Command` subclasses; the mixin adds a second axis of behaviour without altering the primary hierarchy.

**Context Manager** — for resources with bounded lifetimes (e.g., `stats.FolderStats`, `stats.FileStats`). Implement `__enter__` / `__exit__`; do not manage resource lifetimes via `__init__` and `__del__`.

---

## Output

Use the `show` module for all user-facing output. Never use `print()` or the `logging` module.

| Function | Use for |
|---|---|
| `show.important(message)` | Highlights, section headers |
| `show.normal(message)` | Regular progress messages |
| `show.verbose(message)` | Detail shown only when `--verbose` is passed |
| `show.error(message, exception)` | Fatal errors with traceback |
| `show.rule()` | Visual separator between processing phases |

`show.set_verbose(args.verbose)` is called once in `cli.py`. Call `show.verbose()` freely; the module manages the gate.

---

## Input validation

Validation is applied aggressively at every internal API boundary — not just at external input. This is more defensive than typical Python code and is an intentional project convention.

**Always use the `check` module.** Do not write inline guards (`if x is None: raise`, `if not isinstance(x, T): raise`). If no existing `check` function covers the case, add one to `check.py`.

**Validate all constructor parameters** at the top of `__init__`, before any other logic:

```python
def __init__(self, folder: pathlib.Path, strategy: OutputFilePathStrategy):
    check.ensure_folder(folder)
    check.ensure_type(strategy, OutputFilePathStrategy)
    self.__folder = folder
    self.__strategy = strategy
```

Validate at every point where values of uncertain provenance enter: constructors, strategy interface methods, and any method that first consumes user input, filesystem data, or config values. Assembly helpers that receive internally-constructed, already-validated values do not need to re-validate.

**Validation layering for paths** — always check type first, then existence and kind:
- `check.ensure_path(x)` — confirms `x` is a `pathlib.Path`
- `check.ensure_file(x)` — confirms it is a `pathlib.Path` and an existing file
- `check.ensure_folder(x)` — confirms it is a `pathlib.Path` and an existing directory

**Domain constraints** — apply range and format checks for constrained values: `check.ensure_int_between`, `check.ensure_int_positive`, `check.ensure_str_startswith`, `check.ensure_list_non_empty`.

**Strategy types** — when a strategy object is accepted as a parameter, validate its type with `check.ensure_type(x, ExpectedStrategyBase)`.

---

## Error handling

Define custom exception classes for anticipated failure conditions:

```python
class SomethingFailedError(Exception):
    MESSAGE = "Descriptive message with '{placeholder}'."

    def __init__(self, value: str):
        self.message = self.MESSAGE.format(placeholder=value)
        super().__init__(self.message)
```

When wrapping exceptions from third-party libraries, use exception chaining:

```python
raise ShellCommandRuntimeError(name, e) from e
```

Do not add catch-all handlers inside commands or processing classes. The top-level handler in `main()` catches `KeyboardInterrupt` (exit code `130`) and `Exception` (exit code `1`); let unexpected errors propagate there.

---

## Shell commands

Use the `sh` library via `shell.ShellCommandFileProcessor`. Do not use `subprocess`. Do not call `sh.Command` directly outside `shell.py`.

Subclass `ShellCommandFileProcessor` for commands that invoke a shell tool per file:
- Verify the command is available during `__init__` (the base class handles this).
- Implement `_finalize_args` to build the argument list with input and output file placement.
- Implement `_get_verify_args` if the bare command is not a valid availability probe.
- Raise custom shell errors by chaining from the underlying `sh` exception.

---

## Dry-run behavior

All file-modifying operations must respect the `dry_run` flag. When `dry_run=True`:

- Do not create, move, rename, delete, or overwrite files.
- Still validate inputs.
- Still compute intended output paths.
- Still show what would happen via `show`.
- Emulate enough results for statistics reporting to remain meaningful.

---

## Comments

Organise methods in a class into sections with a comment header when the class contains multiple well-defined groups:

```python
# Private methods

# Abstract methods

# Public methods
```

Write inline comments only when the *why* is non-obvious: a hidden constraint, a subtle invariant, or a workaround. Do not describe what the code does. One line per comment block.

---

## Docstrings

Write a class-level docstring for abstract base classes and for classes whose contract is non-obvious from the name alone.

Write a method docstring when the expected behaviour requires explanation for implementors — particularly for abstract methods with non-trivial contracts (see `_get_common_arguments_defaults` in `commands.py`).

No docstring is required for concrete subclasses, simple methods, or property getters.

---

## Testing

Tests are integration tests that invoke real external tools (`rawtherapee-cli`, `convert`, `ffmpeg`). Do not mock these tools.

Every new behaviour requires tests. Every bug fix requires a regression test.

- Test files: `{module}_test.py` (e.g., `video_test.py`) — not `test_{module}.py`
- Test functions: `test_{ClassName}_{method}_{scenario}` (e.g., `test_Command_get_post_processing_strategy`)
- Use `tmp_path` (function-scoped) and `tmp_path_factory` (module-scoped) for temporary filesystem state
- Static test data (sample media files, config files) goes in `tests/data/{command}/`

`monkeypatch` is permitted for infrastructure and platform concerns where no real tool exists to invoke (e.g., stubbing `importlib.metadata.version()` to test version detection logic). It must not be used to substitute external CLI tools that commands invoke.

Structure each test module in two sections:
1. Input validation — verify that invalid inputs raise the expected exception
2. Core logic — verify correct output on valid inputs using real tool execution. Necessary part of core logic is `dry_run` mode. The dry-run test must verify that the state of test data has not changed, i.e., no real actions were executed.

---

## Keeping this document current

When a convention changes, update this document in the same commit as the code or configuration that establishes the new convention.
