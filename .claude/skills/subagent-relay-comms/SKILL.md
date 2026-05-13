---
name: subagent-relay-comms
description: Instructions for subagents (AA, Coder) when communicating with PO through PM relay
user-invocable: false
---

# Relay Communication Protocol

This protocol defines how you (subagent) communicate with PO through PM relay.

## Outbound — sending messages to PO

Every outbound message must use the `#PO:` prefix. PM relays all subagent communication to PO; there are no internal messages that you direct to PM; PM is only a relay. The prefix lets PM distinguish subagent content worth relaying, and the explicit recipient maintains protocol consistency. This format must be followed for every message, otherwise it will not reach PO.

`#PO:` is stripped before relaying to PO.

You cannot use the AskUserQuestion tool directly, it is not available for subagents. To ask PO a choice-based question, use the structured `--QUESTION--` format (see below). PM translates it into an AskUserQuestion for PO.

Example — free-form message:

```
#PO: I've completed the analysis. We should use JSON format for config files.
```

### Structured questions

When you need PO to make a choice, combine optional free-form context with a `--QUESTION--` block. The structured question template is:

```
--QUESTION--
<Question text>
--OPTIONS--
1. <Choice 1>
2. <Choice 2>
--ENDQUESTION--
```

The QUESTION block must come last — nothing follows it.

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
PM detects the `--QUESTION--` block, translates it into an interactive question (AskUserQuestion) for PO, and relays the answer back to you.

## Inbound — receiving responses from PO

Responses from PO arrive via PM relay with a `#PO:` prefix:

```
#PO: Let's go with JSON.
```

## Terminal — final response

When you terminate (complete or escalate), PM relays your structured final response verbatim to PO. PM reads and interprets the outcome to determine next steps; you will not be contacted again in this session.

The final response must still start with `#PO:` but cannot contain a `--QUESTION--` block.
