# molim

[![CI](https://github.com/nightjarrr/molim/actions/workflows/ci.yml/badge.svg)](https://github.com/nightjarrr/molim/actions/workflows/ci.yml)
[![Release](https://github.com/nightjarrr/molim/actions/workflows/release.yml/badge.svg)](https://github.com/nightjarrr/molim/actions/workflows/release.yml)
[![codecov](https://codecov.io/gh/nightjarrr/molim/branch/main/graph/badge.svg?token=NCL8ZXUHYJ)](https://codecov.io/gh/nightjarrr/molim)

A unified CLI for running batch operations over files in a folder on Linux —
wraps external tools behind a single, consistent interface.

*"Molim" means "please" in Croatian, Serbian, Bosnian, and Montenegrin — a polite
way to ask for something useful to be done.*

---

## What it does

Many useful command-line tools have their own interfaces, flags, and conventions.
molim provides a single, consistent entry point for running batch operations over
files in a folder — regardless of the underlying tool doing the work.

The current command set focuses on image and video processing, wrapping
[RawTherapee](https://rawtherapee.com/), [ImageMagick](https://imagemagick.org/),
and [FFmpeg](https://ffmpeg.org/), but the design is not limited to these use cases.

Point it at a folder, pick a command, and it handles the rest.

---

## Requirements

- **Linux** (no other platforms are tested or planned for support)
- **Python 3.12+**
- The following tools installed and available on `PATH`:

| Tool | Used for | Install (Debian / Ubuntu) |
|---|---|---|
| [RawTherapee](https://rawtherapee.com/) | RAW file processing | `sudo apt install rawtherapee` |
| [ImageMagick](https://imagemagick.org/) | Format conversion, resizing | `sudo apt install imagemagick` |
| [FFmpeg](https://ffmpeg.org/) | Video processing | `sudo apt install ffmpeg` |

---

## Installation

*Installation instructions will be added once the first release is published.*

---

## Commands

```
usage: molim [-h] [--version]
             [jpegify | rawtherapee | rawtherapee-hq | resize | suffix | video]
             ...
```

| Command | Description |
|---|---|
| `jpegify` | Convert images of other formats into JPEG using ImageMagick |
| `rawtherapee` | Process image files with RawTherapee profiles |
| `rawtherapee-hq` | Process image files with RawTherapee profiles (high-quality JPEG variant) |
| `resize` | Resize images using ImageMagick |
| `suffix` | Add a suffix to file names |
| `video` | Process and optimise video files using FFmpeg |

Run `molim --help` for general help, or `molim <command> --help` for
per-command options.

---

## Notes

- **Linux only.** There are no plans to support Windows or macOS.
- **Use at your own risk.** Always back up your files before processing — batch
  operations on large folders can be destructive if misconfigured.
- **Personal project.** The primary goal is to be useful to the author.
  Features and design decisions reflect personal workflows and preferences. PRs from external contributors are not being accepted.
- **Feel free to fork** and adapt to your liking if you find it useful but not exactly fitting your needs.

---

## License

MIT — see [LICENSE](LICENSE) for details.
