# Changelog

## UPCOMING

## v0.3.6 — 2026-04-20

- Added `--version` flag to the CLI. (#3)
- Added MIT License. (#5)

## v0.3.5 — 2026-04-19

- Added AVIF and HEIC as supported input formats for the `jpegify` command. (#1)
- Increased default RawTherapee output JPEG quality (quality 80, subsampling 2). (#2)

## v0.3.4 — 2026-04-15

- Added `rawtherapee` command for batch RAW file processing via RawTherapee.
- Added `suffix` command to batch-append suffixes to filenames.
- Added `--suffix` option to the `resize` command.
- Added a configuration file to define a global file-skip strategy.
- RawTherapee profile folder and profile name can now be set in the config file.
- Long filenames are now truncated in the progress bar for readability.
- Ctrl+C now exits cleanly with a graceful message instead of a traceback.
- Improved help text for all commands.
- Fixed display of filenames containing brackets in the progress bar.
- Project renamed to `molim`.
- ...and much, much more that was left undocumented but awesome.
