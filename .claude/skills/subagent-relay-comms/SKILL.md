---
name: subagent-relay-comms
description: Concrete relay communication instructions for subagents (AA, Coder) when operating through PM relay
user-invocable: false
---

# Subagent Relay Communication

You are operating through PM relay. Your counterpart for interaction with the Project Owner (PO) is the PM. All messages to PO flow through PM; all responses from PO arrive through PM.

## Outbound — sending messages to PO

Prefix every PO-directed message with `#PO:`. PM strips this prefix before relaying to the PO.

Example — free-form message:

```
#PO: I've completed the analysis. We should use JSON format for config files.
```

### Structured questions (QUESTION format)

When you need PO to make a choice, combine free-form context with a `--QUESTION--` block. The QUESTION block must come last — nothing follows it.

Example:

```
#PO: I'm evaluating config formats. JSON has wide support but no comments.
YAML is more human-readable but parsing is more complex.

--QUESTION--
Should we use JSON or YAML for config files?
--OPTIONS--
1. JSON
2. YAML
3. Other (specify)
--ENDQUESTION--
```

PM detects the `--QUESTION--` block, translates it into an interactive question (AskUserQuestion) for PO, and relays the answer back.

## Inbound — receiving responses from PO

Responses from PO arrive via PM relay with a `#PO:` prefix:

```
#PO: Let's go with JSON.
```

## Terminal — final response

When you terminate (complete or escalate), PM relays your structured final response verbatim to PO. PM reads and interprets the outcome to determine next steps; you will not be contacted again in this session.
