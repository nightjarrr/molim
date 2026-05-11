---
name: aa-spec
description: Reference knowledge for Associate Architect when drafting or revising a functional specification (spec.md). Covers required content, discovery discipline, acceptance criteria quality, and decision logging.
user-invocable: false
---

# AA Phase Skill — Functional Specification (Phase 2)

This is a reference document. Invoke it at the start of a Phase 2 session to load the knowledge and discipline required to produce a high-quality `spec.md`.

---

## What spec.md must contain

A complete `spec.md` has all of the following sections. Do not omit any; if a section genuinely has no content for this issue, say so explicitly (e.g., "None — this change does not affect existing functionality").

1. **Problem statement / motivation** — Why is this needed? What gap or friction does it address? Written so a reader unfamiliar with the immediate context can understand the case for the change.
2. **Functional requirements** — What the system must do, from a user perspective. Use "must", "should", "must not" language. Enumerate individual requirements; do not write a single prose paragraph that bundles multiple requirements together.
3. **Out of scope** — Explicit exclusions. Naming something out of scope is as important as naming it in scope; it prevents scope creep and helps reviewers calibrate expectations.
4. **Acceptance criteria and verification scenarios** — Observable, independently testable conditions that must hold when the feature is complete. Written from the user's perspective; each criterion must be verifiable without access to implementation internals.
5. **Impact on existing functionality** — What existing behaviors, commands, or workflows are affected? What stays the same? If none, say so.
6. **Alternatives considered and rejected** — At least two alternatives that were evaluated. For each: what it is, what forces favor it, and why it was rejected in favor of the chosen approach.
7. **Decision log** — The record of decisions made during elaboration with the Project Owner, including the date, the question raised, the decision taken, and the forces that drove it.

---

## Requirements elicitation discipline

The Project Owner states requests, not requirements. A request ("I want users to be able to set X") embeds a solution. The requirement is the underlying intent ("users need control over Y so they can achieve Z"). Your job is to extract the intent before committing it to paper.

**Ask "why" before "what."** When a request arrives, probe the motivation before asking about details. The answer to "why" often reveals that the stated solution is not the only one — or not even the best one.

**Distinguish requirements from solutions.** A requirement states a need or constraint. A solution states a mechanism. Requirements belong in spec.md; solutions belong in tech-design.md. When the PO proposes a solution directly, reflect it back as a requirement question: "Is the underlying need X? Or is the solution itself the requirement because Y?"

**Surface hidden constraints.** Some constraints are unstated because the PO assumes them as obvious. Common categories: backward compatibility, performance bounds, platform restrictions, security invariants, operational constraints (e.g., must work without network access). Probe each category relevant to the issue.

**Avoid scope creep.** Related work has a way of attaching itself to in-flight features. When something adjacent surfaces during discovery, record it in the decision log as "noted but deferred" rather than absorbing it into scope. A deferred item is a candidate for a new issue.

---

## Interview mode

When the Project Owner requests structured requirements elicitation — or when the incoming issue lacks sufficient detail to draft meaningful functional requirements — enter interview mode.

In interview mode:
1. Announce that you are entering a structured elicitation conversation.
2. Work through a prepared question list, one question at a time. Do not ask multiple questions in a single message; that fragments focus and produces lower-quality answers.
3. Cover the following dimensions systematically, stopping when a dimension is clearly not applicable:
   - **Problem and motivation** — What problem does this solve? For whom? How is it currently handled?
   - **Core behavior** — What must the system do? What inputs does it take? What outputs does it produce?
   - **Boundaries** — What is explicitly not in scope? What adjacent functionality should not change?
   - **Acceptance** — How will you know it is done? What would a successful demo look like?
   - **Constraints** — Performance, security, backward compatibility, platform, or operational constraints.
   - **Alternatives** — Have alternative approaches been considered? What were they? Why rejected?
4. After the question list is exhausted, summarize what you've heard and ask for confirmation before transitioning to drafting.

Interview mode is not a rigid script. Adapt the question order and depth based on answers received. Skip dimensions that are clearly not applicable. Add follow-up questions when an answer raises something important.

---

## Acceptance criteria quality

A good acceptance criterion is:
- **Observable** — it can be confirmed by testing or inspection without reading the code.
- **User-perspective** — it describes what the user or system does, not what a unit test asserts.
- **Independently verifiable** — one criterion does not depend on another being true first.
- **Specific enough to fail** — a vague criterion ("works correctly") is not a criterion; a specific one ("processing 1000 files completes in under 30 seconds") is.

Each criterion should map cleanly to one or more test scenarios that Coder will write in Phase 5. If you cannot imagine a concrete test for a criterion, rewrite it until you can.

Avoid criteria that are just restatements of requirements (e.g., a requirement that says "must support X" and a criterion that says "X is supported" add nothing). Criteria should specify the conditions under which the requirement is considered fully satisfied — edge cases, boundary conditions, error cases.

---

## Decision log discipline

The decision log is not a summary of what was decided. It is a record of the reasoning that led to each decision, so that future reviewers — including AI agents in later phases — can understand why things are the way they are without reconstructing the conversation.

Each entry must include:
- **Date** — when the decision was made.
- **Question** — the specific question or tension that required a decision.
- **Forces** — what considerations were in tension (e.g., simplicity vs. flexibility, familiarity vs. correctness, backward compatibility vs. clean design).
- **Decision** — what was chosen.
- **Rationale** — why this option was chosen over the alternatives given the forces.
- **Rejected alternatives** — briefly, what was not chosen and why not.

Do not conflate the decision log with the "Alternatives considered" section. The alternatives section describes the design space; the decision log captures the specific decision moments and their reasoning.

---

## Discovery conversation structure

A good discovery conversation has a structure:

1. **Opening** — restate the issue in your own words and ask the PO to confirm or correct. This surfaces misreading early.
2. **Scope establishment** — identify the core problem and the boundary of the change. Name adjacent things that are not in scope.
3. **Requirements extraction** — go deep on what the system must do, using the elicitation discipline above.
4. **Constraint identification** — probe for unstated constraints before they become surprises in Phase 5.
5. **Alternatives brief** — briefly surface the two or three most plausible approaches and ask the PO to weigh in or confirm your preferred direction. This primes the alternatives section.
6. **Summary and confirmation** — before drafting, summarize: "Here is what I understood. Here are the requirements. Here is what is out of scope. Here are the key decisions. Ready to proceed?"

The transition from discovery to drafting is gated on explicit PO confirmation. Do not begin writing spec.md until PO has confirmed the discovery summary.
