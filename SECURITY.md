# Security Policy

## Supported versions

Only the latest release of **molim** receives security fixes. No backports are
made to older versions.

## Reporting a vulnerability

If you discover a security vulnerability in **molim**, please **do not open a
public GitHub issue**. Instead, report it privately using GitHub's
[Report a vulnerability](https://github.com/nightjarrr/molim/security/advisories/new)
feature.

Please include:
- A description of the vulnerability
- Steps to reproduce it
- Any relevant environment details (OS, **molim** version, tool versions)

## What to expect

This is a personal project maintained by a single author. There is no formal
response SLA. Reported vulnerabilities will be reviewed and addressed on a
best-effort basis. You will receive a response when the issue has been
assessed.

## Scope

**molim** is a local CLI tool with no network-facing components, no authentication
mechanisms, and no persistent storage beyond local files. Its attack surface is
limited to the local system it runs on and the files it processes.

Vulnerabilities in the underlying tools (RawTherapee, ImageMagick, FFmpeg, etc)
should be reported to their respective projects, not here.
