---
name: Asymmetric difficulty — know when to stop and ask
description: When tasks are asymmetrically hard for the agent vs. the user, stop early and describe the problem instead of escalating complexity.
type: feedback
originSessionId: b0d9351e-c60c-441a-bbc6-8007ebeed38f
---
When multiple attempts at the same goal fail, the complexity of workarounds escalates, or the path involves risky hacks — stop and describe the problem to the user. The thing that is impossibly complex through the CLI/API may be a 5-second click in a web UI for the user.

**Why:** This is codified in the CLAUDE.md "partnership" section. Continuing to bash at an API that isn't cooperating wastes time and risks breaking things. The user and agent have complementary capabilities — the user sees this as the agent using good judgement, not as a failure.

**How to apply:** After 1-2 failed attempts at a non-trivial goal (especially with external APIs), stop and describe what you're trying to accomplish, what you've tried, and why it's not working. Propose handing off the human-friendly part to the user.
