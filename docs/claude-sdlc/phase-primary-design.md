# Phase-Primary Design

This document defines the Claude Code implementation architecture for the Agentic SDLC. It translates the platform-agnostic design in `docs/AGENTIC-SDLC.md` into concrete Claude Code primitives.

**Status:** Proposal — architectural direction emerging from triage exploration of #136. Not a final decision. Open questions noted at end.

**Scope:** This design covers the feature workflow only (Phases 1–7 for a single issue). The release workflow — coordinating multiple merged issues into a versioned release — is a distinct flow with different coordination needs and is not addressed here. It will require a separate design addendum.

---

## Core concept

The **phase-primary design** rests on one observation about the SDLC: phases are strictly sequential, and each phase has exactly one owning role. At any moment there is exactly one agent that needs to be active and talking to PO. There is never a need for two agents to be simultaneously active on the same feature.

The mental model is a **slideshow**, not parallel swimlanes. Each slide is a phase; each phase has one agent on stage. When the slide advances, the previous agent exits and the next one enters with full context reconstructed from durable artifacts.

This has a direct consequence: relay is unnecessary. If AA is the active agent for Phase 2, AA simply *is* the primary Claude Code session. PO talks to AA directly. PM is not in the room. When AA is done, PM comes back on stage.

---

## Alternatives considered

Three approaches were analyzed as part of the triage exploration. This section captures what was learned from each — it informs the proposal but does not represent a final decision on any of them.

**Subagents + relay** (`relay-protocol.md`): PM is the primary session by default — that is a consequence of PM being the container's default CMD, not of the relay. When PM dispatches AA or Coder as subagents, PO cannot communicate directly with the subagent; all messages flow through PM via the relay protocol, a narrowly-scoped message-passing mechanism. The relay's own problems are significant: background-resumed agents auto-deny permission prompts (hard platform constraint — AA cannot write files when resumed via SendMessage); relay is structurally unstable because PM interprets content it should pass transparently, producing content fabrication and message loss in the first live session. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`.

**Agent Teams**: PM as team lead, AA and Coder as teammates with direct PO access. Designed for parallel independent workers with minimal human involvement; SDLC is sequential with high human involvement — a mismatch in workflow shape. Same experimental flag as relay; teammates lost on `/resume`. Significantly higher token cost.

**Merged PM/AA (skills-based)**: PM and AA collapse into one primary session; Coder remains as a fire-and-forget subagent. Destroys the role separation that is fundamental to the SDLC design. With Coder as the only remaining agent, the architecture is a monolith in practice.

**The common thread**: in all three approaches, PM is the permanent primary session and AA/Coder are secondary. PM becomes primary simply by being the default Claude Code session — a structural consequence of the container CMD, not something the relay controls. The relay is a separate, narrow protocol layered on top for message passing; its problems are its own. The deeper issue is the underlying model: the Agent tool is designed for fire-and-forget delegation, not for dispatching interactive sessions that need deep conversational access to PO. AA's phases require exactly that — and these cannot be adequately served through a secondary session regardless of how well the relay works.

---

## The conductor

The **conductor** is the container's default CMD. It replaces the current behavior of launching a single PM Claude Code session as the container's main process.

The conductor implements a **state machine** over GitHub issue phase labels. Each SDLC phase is a state; transitions are triggered by successful phase completion (advance to next phase) or failure conditions (invoke PM for judgment). For each state, the conductor determines the correct agent, launches it, reads the handoff, and drives the transition:

```
current state = read phase label from GitHub issue

loop:
  1. validate prerequisites for current state
     (branch exists, expected artifacts present, issue is open)
  2. if validation fails → invoke PM agent with failure context; read PM handoff; decide
  3. determine agent and invocation mode for current state (see mapping below)
  4. write dispatch brief
  5. launch: claude [--flags] --agent <name>
     blocks until PO explicitly exits the Claude Code session (returns control to conductor)
  6. read handoff document committed to branch by agent
  7. present PO gate with conductor's suggested action based on handoff status:
       a. proceed to next phase  (suggested when handoff is complete)
       b. invoke out-of-phase PM  (suggested when handoff is escalated or partial)
       c. end the loop and exit
  8. if proceed:
       post handoff summary as GitHub issue comment
       transition: advance phase label → new current state
       if issue lifecycle done → exit
       continue loop
  9. if invoke PM:
       invoke PM agent with context; read PM handoff; return to gate
  10. if end:
       exit
```

The conductor owns all GitHub write operations (label updates, issue comments). Phase agents do not write to GitHub directly — the conductor does, after reading each handoff.

**PO session exit**: at the end of a phase session, PO is responsible for explicitly exiting the Claude Code REPL (e.g. typing `/exit`) to return control to the conductor. The conductor blocks on the agent process and cannot proceed until the session terminates.

**PO gates**: the conductor pauses between phases and presents PO with explicit choices before taking any action. The conductor offers a suggested action based on the handoff status, but PO retains full control — they can accept the suggestion, call for an out-of-phase PM session to assess the situation, or end the loop entirely. The gate is what makes the conductor a supervised state machine rather than a fully autonomous one.

**Container lifetime** is still PO-controlled. PO can exit the conductor loop (Ctrl+C) at any time. A single container run may cover one phase or many — the same choice as today.

**Launcher override**: the host launcher can pass a different CMD to run vanilla `claude` for out-of-SDLC work. The host has no knowledge of SDLC specifics.

---

## Agent invocation patterns

Two invocation modes are available. The `--agent` flag selects the role; the presence or absence of `-p` selects interactive vs. non-interactive execution.

### Interactive

```bash
claude --agent <name>
```

Foreground primary session. PO talks directly to the agent. No relay. Used for AA across all design phases, and for PM — both at phase-owning steps (triage, PR) and out-of-phase when the conductor cannot proceed deterministically and needs judgment.

### Non-interactive

```bash
claude -p --agent <name>
```

Print mode. The agent executes, produces output, and exits without an interactive session. The conductor reads the result. `--output-format json` can be added to make the output machine-readable.

The one-flag difference between modes is intentional: non-interactive enforces fire-and-forget at the platform level, not just by convention.

**Coder's mode is an open question.** Coder may run non-interactively (fire-and-forget; conductor reads output directly) or interactively (same as AA and PM; Coder surfaces questions to PO during implementation). See Open questions.

---

## Phase-to-agent mapping

| Phase | Label | Agent | Mode |
|---|---|---|---|
| 1 — Triage | `phase: triage` | PM | Interactive |
| 2 — Spec | `phase: spec` | AA | Interactive |
| 3 — Tech Design | `phase: tech-design` | AA | Interactive |
| 4 — Impl Plan | `phase: impl-plan` | AA | Interactive |
| 5 — Impl Coding | `phase: impl-coding` | Coder | Non-interactive |
| 6 — Impl Docs | `phase: impl-docs` | AA | Interactive |
| 7 — Pull Request | `phase: impl-done` | PM | Interactive |

---

## Dispatch brief

Before launching a phase agent, the conductor writes a dispatch brief and passes it to the agent at launch. The brief provides everything the agent needs to begin work:

- Issue ID, title, type
- Current phase and expected deliverable
- Paths to prior artifacts (spec.md, tech-design.md, etc.) as applicable
- Any relevant findings from the previous phase's handoff

The dispatch brief is the successor to the subagent dispatch input that PM previously constructed when invoking AA or Coder via the Agent tool. It serves the same purpose — providing a self-contained task context — through a different mechanism.

The brief is ephemeral: written before each agent launch, not persisted beyond the session. Format and delivery mechanism are implementation details.

---

## Handoff document

At phase completion, the agent writes a handoff document and **commits it to the feature branch** before PO exits the session. The conductor reads it after the agent process exits.

**Why committed to branch**: the container is ephemeral. Between container runs, only durable artifacts survive. Committing the handoff to the branch ensures the conductor can read it on a fresh start, the same way it reads spec.md or tech-design.md.

The handoff must communicate: completion status, paths to artifacts produced, findings worth surfacing to PM, and any deviations from the plan. Format and location are implementation details.

The handoff replaces the structured "final response" terminal output that AA and Coder previously produced for PM relay. Content is equivalent; delivery mechanism changes from console output (read by PM in the same session) to a committed artifact (read by the conductor after process exit).

After reading the handoff, the conductor posts its content as a GitHub issue comment and advances the phase label.

---

## PM's revised role

In the current proto-SDLC, PM is the permanent primary session — always active, present for all phases. In the phase-primary design, PM is an on-call agent:

- **Happy path**: the conductor handles phase transitions, label updates, and GitHub state updates deterministically. No PM agent invocation needed.
- **Out-of-phase**: PM is invoked when judgment is required — validation failures, escalations, cross-issue coordination decisions the conductor cannot resolve deterministically. PM handles the situation interactively with PO, writes a handoff, exits.

PM's cross-issue coordination capabilities remain intact. Between phases, the conductor reads GitHub state (labels, comments, links). When something requires PM judgment, PM reconstructs cross-issue context from GitHub at session start — the same approach the SDLC design has always intended.

---

## CLAUDE.md

CLAUDE.md becomes lean: minimal orientation that every agent needs regardless of role.

Contents:
- Project name, purpose, and technology
- Repository structure (source, tests, docs, agent definitions)
- Pointers to `docs/architecture.md` and `docs/conventions.md`

Role-specific instructions, phase workflows, and SDLC procedures move entirely into the respective agent definitions and skills. CLAUDE.md no longer carries PM workflow.

---

## What this replaces

| Current | Replaced by |
|---|---|
| PM as permanent primary session | Conductor loop + on-call PM agent |
| Subagent relay (SendMessage, `#PO:` protocol) | Direct PO interaction in foreground sessions |
| `relay-protocol.md` / `subagent-relay-comms` skill | Obsolete — retire both |
| AA's `gh issue develop` exception (github:write) | Conductor handles branch creation as part of Phase 1/2 setup |
| "Final response" terminal output format | Handoff document committed to feature branch |
| CLAUDE.md with full PM workflow | Lean orientation; role behavior in agent definitions |

---

## Open questions

**Handoff format and location**: structure, file format, and path within the branch are implementation details to be defined during design. The conceptual requirements are clear: status, artifact paths, findings, deviations.

**Coder invocation mode**: Coder may run interactively (direct PO access, same as AA and PM) or non-interactively (fire-and-forget, conductor reads output). The tradeoff: non-interactive enforces Coder's narrow role at the platform level but requires a separate escalation path; interactive allows Coder to surface questions mid-run but requires PO attention during implementation.

**Coder escalation path**: if Coder runs non-interactively and escalates, the conductor invokes PM to handle the situation with PO. If PM determines the impl-plan needs amendment before Coder can continue, the protocol for that cycle needs to be specified.

**Conductor implementation**: technology not defined — to be decided during design. The state machine logic, GitHub API requirements, and process management needs inform the choice.

**Session naming**: using `--name` to give each agent session a meaningful display name (e.g., `AA Phase 2 #136`) improves observability when multiple sessions appear in history. Naming convention to be defined.

**`docs`-type issue workflow**: `docs`-type issues skip Phases 3–6 and go directly from Phase 2 to Phase 7. The conductor's phase mapping needs a branch for issue type.
