# Relay Communication Protocol

The relay protocol defines how Project Manager (PM), subagents (Associate Architect, Coder), and Project Owner (PO) communicate when PM dispatches subagents using Claude's Agent tool and SendMessage.

## Roles

| Short name | Full name | Role |
|---|---|---|
| AA | Associate Architect (AA) | Designs SDLC artifacts (specs, tech-designs, impl-plans, docs) |
| PM | Project Manager (PM) | Orchestrator — dispatches subagents, relays communication, manages GitHub state |
| Coder | Coder | Writes code and tests per impl-plan |
| PO | (no full name required) | Human user setting requirements, reviewing documents and code; primary stakeholder |

## Agent identity

Each agent definition declares a `color` in its frontmatter. PM uses the hardcoded color value for that agent in relay headers. Colors are implementation-level — they match the agent's `color` frontmatter field.

### Color-to-emoji mapping

The emoji corresponds to the agent's configured color:

| `color` value | Emoji |
|---|---|
| red | 🔴 |
| blue | 🔵 |
| green | 🟢 |
| yellow | 🟡 |
| purple | 🟣 |
| orange | 🟠 |
| pink | 🩷 |
| cyan | 🩵 |

### Header format

PM outbound messages use the full agent name with the short name in parentheses.

For example:

```
<emoji-aa> Associate Architect (AA):   # relayed AA message
<emoji-coder> Coder:                      # relayed Coder message
<emoji-pm> Project Manager (PM):       # PM's own message
```

## Message routing

All routing uses short names (`#AA`, `#Coder`, `#PM`, `PO`) as markers. Full names are for display only.

## Subagent view

The subagent (AA or Coder) communicates with PO exclusively through PM relay. All outbound communication from a subagent is prefixed with `#PO:`.

### Outbound

Every message from a subagent to PO uses the `#PO:` prefix:

Example:

```
#PO: I've completed the analysis. The best approach is to use JSON format
for config files because it has wide library support.
```

The subagent can combine free-form context with a structured question. The structured question must come last:

Example:

```
#PO: I'm evaluating config formats for the new module. JSON has wide
support but doesn't allow comments. YAML is more human-readable.

--QUESTION--
Should we use JSON or YAML for config files?
--OPTIONS--
1. JSON
2. YAML
3. Other (specify)
--ENDQUESTION--
```

PM strips the `#PO:` prefix before relaying to the human PO. When a `--QUESTION--` block is present, PM translates it into an interactive question (see below).

### Inbound

Responses from PO arrive via PM relay with a `#PO:` prefix:

Example:

```
#PO: Let's go with JSON.
```

### Terminal — final response

When the subagent terminates (completes or escalates), PM relays the structured final response verbatim to PO. At this point PM may also read and interpret the result to determine next steps, since no further communication with that subagent session is expected.

## PM view — outbound to PO

### Headers

Every message displayed to PO has a header identifying the origin:

- Subagent message: `<emoji-agent> <Full Name (Short)>:` — followed by the verbatim subagent content
- PM's own message: `<emoji-pm> Project Manager (PM):`

The `#PO:` prefix is always stripped from subagent messages before relay, both for free-form text and `--QUESTION--` blocks.

### Relay markers

When PM routes a PO response to a subagent (resuming the subagent via SendMessage), it may display a transit marker:

For example:

```
<emoji-pm> Project Manager (PM): Sending your response to <emoji-aa> Associate Architect (AA)...
```

This is a PM-to-PO visual indicator that signals that the relay is in flight.

### QUESTION translation

When a subagent message contains a `--QUESTION--` block, PM:

1. Extracts the question text and options
2. Presents the preceding free-form context to PO (with the appropriate subagent header)
3. Creates an interactive question (AskUserQuestion) for PO with the question and options
4. On PO answer, relays the choice back to the subagent as `#PO: <answer>`

## PM view — inbound from PO

### Message splitting

PM splits PO messages by `#<shortname>:` markers and routes each part independently:

- No marker or `#PM:` — message is for PM. PM handles it per SDLC instructions.
- `#AA:` or `#Coder:` — message is for the active subagent. PM forwards verbatim with `#PO:` prefix via SendMessage.
- When multiple recipients are present, each part is routed independently.

### Recipient validation

PM validates that `#AA:` or `#Coder:` targets match the currently active subagent. If PO addresses a subagent that is not the active one (e.g., sends `#Coder:` while AA is running), PM reverts to PO and explains the mismatch.

## PO view

The PO receives messages with clear origin headers. The protocol is transparent — PO sees verbatim subagent content (with the `#PO:` prefix stripped) and can respond to any recipient using `#<shortname>:` markers.

## References

- Agent definitions: `.claude/agents/associate-architect.md`, `.claude/agents/coder.md`
- SDLC workflow: `CLAUDE.md` (proto-SDLC), `docs/AGENTIC-SDLC.md` (target-state design)
- Subagent dispatch: Claude Agent tool with SendMessage
