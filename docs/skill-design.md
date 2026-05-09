# Skill design: choosing the implementation form

When adding a new skill or reusable capability to an agentic system, one of three implementation forms must be chosen. The choice determines cost, determinism, testability, and how much the skill affects the invoking agent's context. This document provides a framework for making that choice consistently.

**Terminology note:** "skill" is used here as a synonym for "capability" or "reusable operation" — a general term for any scoped unit of agent functionality. It does not strictly refer to the "Agent Skill" concept as defined at agentskills.io or any other specific platform standard.

**Platform note:** the Fork + small model form described below relies on subagent dispatch — a capability specific to the Claude harness (Claude Code / Claude API with the Agent tool). Other agentic platforms may not support this form or may implement it differently. The Scripted tool and Full-context forms are broadly applicable across platforms.

---

## The three forms

**Scripted tool** — executable code invoked by the agent, commonly via a Bash command or shell wrapper, but possibly delegating to Python, CLI utilities, or other executables. No model is involved; the skill's behavior depends on explicit inputs, code, and environment state — not on implicit conversation context. Zero LLM cost. The canonical choice when intelligence is not required inside the skill.

**Fork + small model** — a subagent session dispatched with a small model (e.g. Haiku). The subagent operates in an isolated context; only its final output reaches the invoking agent's context. Intermediate reasoning, tool calls, and working state are hidden. The right choice when interpretation or light reasoning is needed but the skill does not require access to the invoking context and cannot interact with the user.

**Full-context skill** — logic that runs inline within the invoking agent's session. The skill has full access to the conversation context, can ask clarifying questions, and can make decisions that depend on prior session state. Everything it does is visible in the main context. The right choice when user interaction or context-dependent reasoning is genuinely required — and the cost in context growth is accepted.

---

## Central diagnostic question

> Is there a genuine use case where intelligence is required **inside** the skill itself?

If **no**: use a Scripted tool.

If **yes**: is the reasoning self-contained — no access to the invoking context needed, no user interaction needed?
- If **yes**: consider Fork + small model — the subagent can reason in isolation and return only its result.
- If **no**: use a Full-context skill.

---

## Comparison table

| Dimension | Scripted tool | Fork + small model | Full-context skill |
|---|---|---|---|
| **LLM cost** | None | Low — small model, isolated session | High — main context tokens consumed on every invocation |
| **Latency** | Near-zero | One additional model round-trip | Inline — no extra round-trip, but skill steps extend session duration |
| **Operation determinism** | High — behavior depends on explicit inputs and environment state, not on implicit LLM context | Low — model behavior varies across runs | Low — varies; prior context state also influences which steps are taken |
| **Output determinism** | High — structured output determined by code and inputs, not model sampling | Low — model-generated content varies in phrasing and detail | Low — varies; shaped by conversation context at invocation time |
| **Needs conversation context?** | No | No — context must be explicitly injected into the subagent prompt | Yes — direct access to the full invoking context |
| **Needs user interaction?** | No | No — produces a result; no back-and-forth possible | Yes — can ask clarifying questions, present options, and iterate |
| **Needs to reason over results?** | No — output is structured and parseable; no model reasoning required | Yes — subagent reasons over raw results and returns a synthesized output | Yes — inline model intelligence handles reasoning over results |
| **Context injection on success** | Minimal — stdout and exit code only | Minimal — subagent final output only; intermediate steps are hidden | Full — all tool calls, reasoning, and intermediate results become part of the context |
| **Context injection on failure** | Minimal — stderr and non-zero exit code | Minimal — subagent output up to failure point; error message | Full — same as success; partial execution state is already in context and cannot be hidden |
| **Output size control** | Predictable — bounded by script design and tool output | Controllable — subagent output can be constrained by prompt instructions | Unbounded — grows with skill complexity and conversation depth |
| **Implementation complexity** | Low — standard scripting or tooling; no model or prompt engineering | Moderate — subagent prompt design and output handling required | Low — inline logic; no scaffolding needed |
| **Maintainability** | High — no model dependency; behavior stable across model updates | Moderate — coupled to subagent prompt and model version | Moderate — behavior can drift with context changes and model updates |
| **Testability** | High — pure input/output; easily tested in isolation | Moderate — model non-determinism complicates assertion-based tests | Low — tightly coupled to invoking context; hard to isolate and test independently |
| **Failure mode of the mechanism** | Script error or non-zero exit code — deterministic, easy to handle | Subagent error or model failure — output may be incomplete or absent | Model error, prompt drift, or context overflow — failure state visible in main context |

---

## Decision guidance

### When to choose Scripted tool

Choose a Scripted tool whenever the skill can be expressed as a procedural operation: running checks, reading files, computing values, invoking CLI tools, or producing structured output from fixed inputs. If no model reasoning is needed — if the skill's behavior depends only on explicit inputs and environment state — a Scripted tool is almost always the right choice.

Scripted tools have the smallest footprint: they inject minimal output into context, have no LLM cost, are fast, and are straightforward to test. Prefer this form by default and only move to a model-based form when the diagnostic question surfaces a genuine need.

**Watch for:** output verbosity. If the invoked tools produce large stdout, the context injection cost rises. Structure the output and truncate or summarize at the script level if needed.

### When to choose Fork + small model

Choose Fork + small model when interpretation or light reasoning is required inside the skill, but the skill does not need to see the conversation history and does not need to interact with the user. The subagent isolation keeps intermediate work out of the main context and limits token cost to the small model.

This form is well-suited for tasks like: parsing and reformatting unstructured output, generating a short summary or report from raw data, or applying a classification decision to a fixed input.

**Watch for:** the temptation to inject large amounts of context into the subagent prompt to compensate for isolation. If the skill genuinely needs deep access to the invoking context to do its work, that is a signal it should be a Full-context skill instead. Also watch for model non-determinism in downstream consumers — if the skill's output is parsed or acted on programmatically, a Scripted tool with deterministic output is likely more appropriate.

### When to choose Full-context skill

Choose Full-context only when the skill genuinely requires one or both of: access to the ongoing conversation context, or the ability to interact with the user. These are real requirements for skills that guide a workflow, ask clarifying questions, or make decisions that depend on what has already happened in the session.

The cost is real: every Full-context skill invocation grows the context permanently, including on failure. Intermediate tool calls, observations, and partial outputs all become part of the conversation that subsequent steps must read. The skill is also the hardest to test in isolation.

**Watch for:** scope creep. Full-context skills can absorb work that belongs in Scripted tool or Fork. If a portion of the skill is deterministic or interpretive but not truly context-dependent, extract it rather than pulling it into the inline skill. Keep the full-context portion as narrow as possible.

### Composite skills

A skill may combine forms internally. A Full-context skill may call a Scripted tool to gather data, then call a forked model to summarize it, then use the main context to decide on a follow-up. That is a valid and often preferable design.

The classification of the skill as a whole should reflect its highest-context component — but that classification should not be used to justify pulling everything into that component. Each internal step should use the cheapest sufficient form. The goal is to keep model-dependent work — and especially full-context work — as narrow as possible within the skill.
