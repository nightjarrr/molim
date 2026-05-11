---
name: aa-impl-plan
description: Reference knowledge for Associate Architect when drafting or revising an implementation plan (impl-plan.md). Covers the required three-section structure, the Coder contract, work breakdown discipline, and the escalation boundary.
user-invocable: false
---

# AA Phase Skill — Implementation Plan (Phase 4)

This is a reference document. Invoke it at the start of a Phase 4 session to load the knowledge and discipline required to produce a high-quality `impl-plan.md`.

---

## What impl-plan.md must contain

`impl-plan.md` has exactly three sections. Their names, order, and roles are fixed.

### Section 1 — Requirements

A focused, self-contained projection of `spec.md` written for Coder. Coder reads `impl-plan.md` and not `spec.md`. Everything Coder needs to understand what the feature must do, what the acceptance criteria are, and what implementation constraints apply must be in this section.

This is a synthesis, not a copy. Translate the user-perspective language of `spec.md` into implementation-perspective language: what must be true when the code is done, what must not happen, what edge cases must be handled, what existing behavior must be preserved.

Acceptance criteria belong here, restated in terms Coder can verify by running code and tests. A criterion like "processing 1000 files completes in under 30 seconds on standard hardware" gives Coder something testable; "the command works correctly" does not.

### Section 2 — Architecture Context

A filtered architectural view of the parts of the system this feature touches. Synthesized from `architecture.md` (existing system shape) and `tech-design.md` (design decisions for this feature, not yet in `architecture.md`).

AA's job here is to filter and distil, not to present the full architecture document. Show Coder the modules, classes, patterns, and contracts that are directly relevant to this implementation. Exclude everything else. Coder should not need to read `architecture.md` or `tech-design.md` to have the right architectural context — this section provides it.

Proportional to complexity. A one-line change may need a single sentence of context ("this adds a case to `_get_file_skip_strategy` in `commands.py`"). A cross-cutting change may need a substantial section with class relationships, pattern names, and interface signatures.

**No new design here.** If AA finds that the implementation requires a design choice not captured in `tech-design.md`, AA must escalate to PM rather than embedding that new design in the Architecture Context section. The boundary is strict: design decisions belong in `tech-design.md`; `impl-plan.md` distils and carries them forward.

### Section 3 — Work Breakdown

An ordered list of implementation steps. Coder works through this list top to bottom. The ordering is execution order — later steps may depend on earlier ones; the order must reflect that.

For each step:
- **Files** — which files are created, modified, or deleted
- **Classes and functions** — which classes are added or modified; which methods are added, changed, or removed; with specific names (not "add a new method" but "add `_get_file_skip_strategy` to `ExampleCommand`")
- **What it does** — a brief description of the change — enough for Coder to understand what the step accomplishes without guessing

Test coverage plan and risk flags are part of the Work Breakdown section, not separate sections:
- **Test coverage plan** — after the implementation steps, list the tests Coder must write. Reference the test case scenarios from `tech-design.md`. Group by class or behavior. Specify test file names and test function name conventions per `docs/conventions.md`.
- **Risk flags** — for steps with meaningful implementation risk (complex logic, tight coupling to existing behavior, tricky async interactions, steps that modify critical shared infrastructure), flag the risk and describe what to watch for.

---

## The impl-plan as Coder's complete contract

Coder operates from `impl-plan.md` alone. This is not a convenience — it is a design principle of the agentic SDLC. Coder does not have access to the PM session history, the PO's original request, or the elaboration conversation with AA. All of that must be distilled into the impl-plan.

The test: after writing the impl-plan, ask yourself whether Coder can implement the feature correctly having read only that document and `docs/conventions.md`. If Coder would need to make design decisions not addressed in the plan, or would face ambiguity about what to build, the plan is incomplete.

Completeness signals:
- Every public interface that Coder must implement is named and described
- Every file Coder must create or modify is listed
- Every constraint that would affect an implementation choice is stated
- The test coverage plan specifies what to test, not just "write tests"

Completeness does not mean verbosity. An impl-plan that lists every step without leaving gaps is complete. An impl-plan that adds explanatory prose for self-evident steps is over-engineered. Calibrate to complexity.

---

## Requirements section: synthesizing from spec.md

The Requirements section is a transformation of `spec.md`, not a copy. The transformation:

1. **Change perspective** — spec.md is user-perspective; Requirements is implementation-perspective. "Users must be able to set the output quality" becomes "the `--quality` flag must accept integers in the range 1–100; values outside this range must be rejected with a specific error message before any file processing begins."

2. **Make implicit explicit** — spec.md's acceptance criteria are verification conditions. Requirements should add the implementation constraints that make them achievable: data types, error handling boundaries, contract invariants.

3. **Preserve completeness** — every requirement from spec.md must be traceable to something in the Requirements section or explicitly called out as not requiring implementation (e.g., a requirement already satisfied by the existing behavior).

4. **Include constraints** — any constraint that would change how Coder implements something belongs here. Platform constraints, backward-compatibility requirements, performance bounds, prohibited approaches.

---

## Architecture context section: filtering and distilling

The Architecture Context section is not a summary of `architecture.md`. It is a targeted view of the subset of architecture that Coder must understand for this specific implementation.

Process:
1. Read `architecture.md` to understand the current system.
2. Read `tech-design.md` to understand the design decisions for this feature.
3. Identify the modules, classes, and patterns that Coder will directly touch or depend on.
4. Write only about those. For each: its role in the system, its interface, and any constraints or conventions Coder must respect when modifying it.
5. Include the design decisions from `tech-design.md` that Coder must apply — the "what to build" is in Requirements, but the "how to structure it" comes from design decisions that are specific to this feature.

The Architecture Context section should answer:
- What already exists that Coder is building on or modifying?
- What patterns does Coder apply and how?
- What are the contracts Coder must respect?
- What design decisions (from tech-design.md) constrain the implementation?

It should not contain:
- Design decisions not yet made (escalate those)
- General architecture background unrelated to this feature
- Explanations of things Coder already knows from `docs/conventions.md`

---

## Work breakdown discipline

The right granularity for a work breakdown step is: a cohesive change to one part of the system that can be understood, implemented, and reviewed as a unit. Not so small that the list becomes a code review checklist; not so large that a step could hide complexity.

Signals that a step is too large:
- It touches more than two files with significant changes in each
- It contains more than one conceptually distinct change (e.g., "add X and also refactor Y")
- Implementing it would require Coder to make design decisions not specified in the plan

Signals that a step is too small:
- It is a single line change with no dependencies or impact
- It could be described as part of an adjacent step without loss of clarity

Each step must be actionable. "Implement the feature" is not a step. "Add `_get_file_skip_strategy` to `ExampleCommand` in `src/molim/example.py` to return a `GreaterThanSizeFileSkipStrategy` based on `args.greater_than`" is a step.

Ordering: put foundational changes (new base classes, shared utilities, configuration) before the steps that depend on them. Put test writing steps after the implementation steps that create the code under test — but note them explicitly; do not leave test coverage implicit.

---

## Escalation boundary

If writing the impl-plan reveals a design gap — something that Coder would need to decide but that hasn't been decided in `tech-design.md` — AA must escalate to PM rather than filling the gap independently.

The boundary: AA is authorized to distil, filter, and synthesize design decisions that are already made. AA is not authorized to make new design decisions in Phase 4. New design decisions belong in Phase 3 (`tech-design.md`), approved by PO.

When to escalate:
- The Architecture Context section would require AA to decide how to structure a new class or interface that isn't addressed in `tech-design.md`
- The Work Breakdown requires specifying a behavior for a scenario not covered by spec.md or tech-design.md
- The Requirements section reveals an ambiguity in spec.md that would cause Coder to make different implementation choices depending on interpretation

Escalation in Phase 4 typically means: "I found a design gap; we need to amend `tech-design.md` before the impl-plan can be completed." PM brings this back to AA as a Phase 3 amendment, or to PO if a requirement question is involved.
