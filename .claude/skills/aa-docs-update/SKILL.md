---
name: aa-docs-update
description: Reference knowledge for Associate Architect when performing post-implementation documentation updates (Phase 6). Covers which documents to examine, the update approach, final coherence read discipline, changelog entry standards, and commit hygiene.
user-invocable: false
---

# AA Phase Skill — Documentation Update (Phase 6)

This is a reference document. Invoke it at the start of a Phase 6 session to load the knowledge and discipline required to perform a thorough and coherent documentation update.

---

## Why documentation consistency matters

`architecture.md` and `docs/conventions.md` are the system's long-term memory. They are the documents that future AA sessions read to understand the system — including your own future invocations. Gaps in these documents compound: a pattern introduced in Phase 5 that is not recorded in Phase 6 becomes an invisible convention that the next AA will not know to follow. Over time, undocumented decisions produce inconsistent designs as each AA session reinvents conventions from context clues.

Documentation updates in Phase 6 are not a formality. They are the act of making the system's evolution legible to future agents and humans.

---

## What to examine

For every Phase 6 session, examine each of the following documents in turn. For each, the question is: "Has the implementation changed this document's domain in any way?"

### architecture.md

Examine for:
- **New modules or files** — if Phase 5 created a new module or moved responsibility to a new file, update the module inventory
- **New classes or patterns** — if a new class hierarchy, abstract base class, or design pattern was introduced or first used, document it
- **New interfaces or contracts** — if Phase 5 established a new public interface that future features will build on, document the contract
- **Changed integration points** — if the feature changed how components connect (e.g., a new hook method on `Command`, a new strategy type, a new step in a processing pipeline), update the relevant section
- **Removed components** — if anything was removed or renamed, update the document to remove or correct references

`architecture.md` describes the current state of the system after implementation. It does not contain design history or rationale (that is in `tech-design.md`) — only the current structure.

### README.md

Examine for:
- **Changed commands** — if a new subcommand was added, or an existing command's flags, arguments, or behavior changed, update examples and reference sections
- **Install instructions** — if new system dependencies (tools that must be on PATH, packages that must be installed) were introduced, update the install section
- **User-facing behavior changes** — if the change affects what a user running `molim` experiences, the README must reflect the current behavior

### conventions.md

Examine for:
- **New patterns introduced** — if Phase 5 established a pattern not previously documented (a new convention for how errors are handled in a specific context, a new way of structuring a class variant, a new naming rule), add it
- **Changed conventions** — if the implementation deliberately departed from an existing convention and that departure is the new standard, update the convention
- **Code style or tooling changes** — if new tools, new tool options, or new formatting rules were introduced, update the tooling section

Do not add conventions that are narrow to one feature. A convention in `conventions.md` must apply broadly enough that future implementations will encounter it and benefit from knowing about it.

---

## Update approach

For each document identified as requiring updates:

1. **Read the full document** — before writing a single word, read the current content end to end. This establishes what exists, avoids duplication, and gives you the context to write a coherent update rather than a bolted-on section.
2. **Identify the affected section(s)** — determine precisely where the update goes. In most cases, this is an existing section that needs new content or correction. In fewer cases, it is a new section.
3. **Write the update** — apply the change. Match the existing document's voice, structure, and level of abstraction. Do not rewrite sections you are not updating.
4. **Re-read the document from the beginning** — after writing, read the full document again. Check for internal consistency: does the new content fit with the surrounding content? Does it contradict anything elsewhere? Does a reader encountering the document for the first time get a coherent picture?

This read-update-read cycle is the minimum. For complex updates touching multiple sections, run it once per section.

---

## Final coherence read

Before committing, perform a final coherence read of every document you updated. Read each one in full, from the beginning. The question is not "is my addition correct" — you already checked that. The question is "does the document as a whole make sense after my changes?"

Specifically look for:
- **Internal contradictions** — two sections that now say different things about the same topic
- **Dangling references** — references to things that were renamed or removed in Phase 5 that you have not yet updated
- **Orphaned content** — content that no longer applies because the thing it describes was changed
- **Missing cross-references** — a new section that should be referenced from elsewhere in the document but isn't

The coherence read is not optional. It is what separates a documentation update that makes the system clearer from one that adds noise.

---

## Changelog discipline

Every Phase 6 documentation update must include a CHANGELOG entry. The entry is added via the Add Changelog Entry skill invocation (which runs the `node scripts/add-changelog-entry.mjs` script directly via Bash).

```bash
node scripts/add-changelog-entry.mjs --issue-id <id> --entry "<entry text>"
```

**Entry quality standards:**

A good entry:
- Is one sentence
- Is written from the user's perspective — what they can now do, or what changed in their experience
- Describes the user-facing value, not the implementation mechanism
- Ends with the issue ID in parentheses: `(#N)` — the script appends this automatically based on `--issue-id`, so do not include it in `--entry`

Good: `Added support for AVIF and HEIC input formats in the jpegify command.`
Bad: `Refactored ImageMagick delegate resolution to use libheif codec bindings.`
Bad: `Fixed a bug.`
Bad: `Issue #65 — AVIF support.`

If the feature has no user-facing change (e.g., an internal refactor with no behavior change), note this in your session output but still confirm with PM whether an entry is appropriate — PM decides based on SDLC policy for this project.

If the feature has multiple distinct user-facing changes, write one entry per change. Each entry must be independently meaningful.

---

## Commit discipline

All documentation changes — updates to `architecture.md`, `README.md`, `conventions.md`, and the CHANGELOG — are committed together in a single commit. Do not split them into separate commits per document.

Commit message format: `Draft docs update for #<id>: <brief summary of what changed>`

Example: `Draft docs update for #65: add AVIF/HEIC support to architecture, conventions, README, changelog`

After committing, push to the feature branch immediately: `git push`.

The documentation commit is distinct from the implementation commits made in Phase 5. Do not amend Phase 5 commits.

---

## Scope check

Phase 6 documentation update is scoped to documenting what was actually implemented. It is not a general documentation audit. If you discover inaccuracies or gaps in the documentation that are unrelated to the current feature, note them in the **Additional findings** section of your final response and flag them as candidates for a new issue. Do not fix unrelated documentation problems in the Phase 6 commit — scope creep in documentation updates creates noisy diffs and makes PR review harder.
