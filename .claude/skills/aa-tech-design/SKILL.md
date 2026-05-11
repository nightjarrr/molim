---
name: aa-tech-design
description: Reference knowledge for Associate Architect when drafting or revising a technical design (tech-design.md). Covers required content, design decision documentation, test case identification, and the boundary between tech-design and architecture.md.
user-invocable: false
---

# AA Phase Skill — Technical Design (Phase 3)

This is a reference document. Invoke it at the start of a Phase 3 session to load the knowledge and discipline required to produce a high-quality `tech-design.md`.

---

## What tech-design.md must contain

A complete `tech-design.md` has all of the following sections. Do not omit any; if a section genuinely has no content for this issue, say so explicitly.

1. **Data model changes** — Any new data structures, schema changes, file format changes, or modifications to in-memory representations. If none, state that explicitly.
2. **Key design decisions and rationale** — The significant design choices made for this feature. Each decision should be documented with the forces considered, the options evaluated, the chosen option, and the rationale. See the decision documentation format below.
3. **Applied design patterns and principles** — Which established patterns from the codebase or general design are applied here, and how. Reference existing patterns by name (Template Method, Strategy, Mixin, Context Manager). If a new pattern is introduced, justify why an existing one was insufficient.
4. **Non-functional requirements** — Performance bounds, security considerations, memory constraints, or other quality attributes that constrain the design. Reference `spec.md` NFRs if any were surfaced.
5. **Identified points of extensibility** — Where the design allows future variation without modification. Distinguish genuine extensibility (a real variant is likely or planned) from speculative extensibility (YAGNI applies).
6. **Affected modules and files** — Which source files, classes, and functions are created, modified, or removed. Be specific enough that a reviewer can navigate to the relevant code.
7. **Test cases and scenarios** — The test scenarios that Phase 5 Coder must implement. Written at design level, not at code level: describe the behavior under test and the conditions, not the assertion code. Cover: normal paths, boundary conditions, error cases, and any scenario that would detect the most likely implementation mistakes.
8. **Dependencies or prerequisites introduced** — New libraries, tools, system packages, or infrastructure that the feature requires. If none, state so. New dependencies require explicit justification; they are not added opportunistically.
9. **Impact on existing functionality** — Which existing behaviors change, which command behaviors or file-format contracts are affected, and how backward compatibility is handled.
10. **Alternatives considered and rejected** — Design-level alternatives. For each: what it is, the forces that favor it, and why it was rejected.
11. **Decision log** — Same discipline as spec.md: each entry records the question, forces, decision, rationale, and rejected alternatives, with dates.

---

## Moving from "what" to "how": translating requirements into design decisions

spec.md answers "what" — what the system must do, from a user perspective. tech-design.md answers "how" — how the implementation will realize those requirements.

The translation is not mechanical. For each requirement in spec.md, ask:

- **What code-level representation does this require?** (Data structures, types, enums, constants.)
- **Where does this behavior live in the existing module structure?** (Which module owns it? Does a new module need to be created? Does an existing class need to be extended or a new one introduced?)
- **Which patterns apply?** (Is this new behavior a new Strategy implementation? A new Command subclass? A Mixin? Or does it extend an existing hook method?)
- **What are the integration points?** (How does the new code connect to the existing pipeline? What contracts does it implement or consume?)
- **What can fail, and where?** (Identify error conditions and specify how they propagate.)

Design decisions emerge from these questions. Each significant choice — where behavior lives, which pattern is used, what the interface looks like — is a design decision that belongs in the document.

Do not confuse implementation detail with design decision. Which variable name to use is not a design decision. Which class hierarchy represents the abstraction is.

---

## Design decision documentation format

Each design decision entry should follow this format:

**Decision:** [one-line description of the choice made]

**Context:** [why this decision was needed — what requirement or constraint forced it]

**Forces in tension:** [the competing considerations — what made this non-trivial]

**Options considered:**
- Option A: [description] — [forces favoring it] — [reason rejected or accepted]
- Option B: [description] — [forces favoring it] — [reason rejected or accepted]

**Chosen:** [which option, and the decisive reason]

**Consequences:** [what this decision makes easier or harder going forward]

Not every decision needs the full template. For straightforward choices, a shorter form (decision, options, chosen, one-sentence rationale) is sufficient. Reserve the full form for decisions with genuine tension or significant downstream consequences.

---

## Test case design at the design level

Test cases in tech-design.md are scenario-level, not code-level. Their purpose is to ensure that Coder's test coverage plan in Phase 4 (impl-plan.md) covers the right behaviors.

For each behavior identified in the design, specify:
- **Scenario name** — short description of what is under test
- **Setup conditions** — the starting state or inputs
- **Action** — what is invoked
- **Expected outcome** — what the correct behavior is

Group test cases into three categories:
1. **Input validation** — invalid or malformed inputs that should be rejected with specific error conditions
2. **Core behavior** — the main paths through the feature
3. **Edge cases and error paths** — boundary conditions, empty inputs, upstream failures, conflicting flags

The test cases here are the specification for what Coder must test. They should be specific enough to prevent gaps, but not so implementation-specific that they lock in a particular code structure.

---

## What belongs in tech-design vs. architecture.md

`tech-design.md` is where new decisions are made and recorded. `architecture.md` is a persistent reference describing the system's current shape.

Put in `tech-design.md`:
- Design decisions made for this feature that are not yet reflected in `architecture.md`
- The reasoning behind those decisions (forces, options, rationale)
- Feature-specific patterns that haven't been established system-wide

Put in `architecture.md` (via Phase 6 documentation update, not here):
- Structural changes that are now system-wide facts after implementation
- New modules, patterns, or integration points that future features should know about

Do not update `architecture.md` in Phase 3. The design hasn't been implemented yet — `architecture.md` reflects the current system, not a proposed future. After implementation is approved in Phase 5, AA updates `architecture.md` in Phase 6.

If you discover during design that the existing `architecture.md` is inaccurate or incomplete, note it in the decision log as a finding but do not update it in Phase 3.

---

## Common pitfalls

**Over-engineering the design.** Adding extensibility for variants that don't exist yet violates YAGNI. If a pattern allows extension, note it; do not design the extension itself. Design is proportional to scope.

**Under-specifying interfaces.** An interface that says "returns a result" is not a specification. Name the types, parameters, and return values. When Coder reads the impl-plan (which summarizes this design), they must be able to write the function signature without guessing.

**Missing alternatives section.** Reviewers need to know what was considered and rejected to assess whether the chosen approach is sound. "We considered X but chose Y because Z" is the minimum. A design without an alternatives section appears unconsidered even if it isn't.

**Conflating tech-design with impl-plan.** tech-design.md answers "how" at the architecture and design level. impl-plan.md answers "what steps does Coder take to build it." Do not put ordered implementation steps in tech-design.md; do not put design rationale in impl-plan.md. The boundary is: design decisions go in tech-design; Coder-facing tasks go in impl-plan.

**Forgetting impact on existing behavior.** Every change has blast radius. Enumerate what doesn't change as well as what does — "file processing behavior is unchanged; only the output path calculation is affected" is a useful sentence for reviewers and for Coder.
