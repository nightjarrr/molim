# Coding Conventions

PEP 8 is the base style. This document lists all points where the codebase intentionally deviates from PEP 8, then covers project-specific conventions that PEP 8 does not address. Apply PEP 8 for anything not listed here.

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

---

## Type annotations

Annotate all function and method signatures — parameters and return types. Use Python 3.12 built-in generics (`list[str]`, `tuple[str, int]`). Do not use `typing.List`, `typing.Tuple`, or other deprecated aliases.

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

One module per command or functional area. Image-processing commands go under `images/`. New commands get their own module file.

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
5. Register the command in `cli.py` by instantiating it in `_create_parser(...)`.

Do not override `_execute` unless there is no other way to achieve the required behaviour. Overriding the template method is a conscious deviation from the established pattern and requires: explicit rationale discussed with and approved by the Project Owner, documentation in the tech design doc for the feature, and a code comment at the override site explaining why the hook methods were insufficient. If overriding is unavoidable, always call `super()._execute(args)` — augment the invocation pipeline, do not replace it.

---

## Design patterns

These patterns are established. Extend them; do not introduce alternatives.

**Template Method** (`commands.py`) — `Command._execute()` orchestrates the processing pipeline. Subclasses implement the hook methods. Never override `_execute`.

**Strategy** (`processing.py`) — pluggable behaviours for output path naming, post-processing, file matching, and file skipping. Add new variants by subclassing the appropriate abstract base: `OutputFilePathStrategy`, `PostProcessingStrategy`, `FileMatchStrategy`, `FileSkipStrategy`, `FileProcessor`.

**Mixin** — for shared argument definitions across multiple command classes (e.g., `ImageMagickMixin` in `images/imagemagick.py`). Use a mixin when the same argparse arguments apply to two or more unrelated command classes.

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

## Error handling

Define custom exception classes for anticipated failure conditions:

```python
class SomethingFailedError(Exception):
    MESSAGE = "Descriptive message with '{placeholder}'."

    def __init__(self, value: str):
        self.message = self.MESSAGE.format(placeholder=value)
        super().__init__(self.message)
```

Use `check` module functions for all input validation (`check.ensure_type`, `check.ensure_not_none`, `check.ensure_int_between`, etc.). Do not duplicate their logic or write inline guards when a `check` function covers the case.

Do not add catch-all handlers inside commands or processing classes. The top-level handler in `main()` catches `KeyboardInterrupt` and `Exception`; let unexpected errors propagate there.

---

## Shell commands

Use the `sh` library via `shell.ShellCommandFileProcessor`. Do not use `subprocess`. Do not call `sh.Command` directly outside `shell.py`.

Subclass `ShellCommandFileProcessor` for commands that invoke a shell tool per file. Implement `_finalize_args` to build the argument list; the base class handles execution and error translation.

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

Structure each test module in two sections:
1. Input validation — verify that invalid inputs raise the expected exception
2. Core logic — verify correct output on valid inputs using real tool execution
