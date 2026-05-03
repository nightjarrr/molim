---
name: ensure-github-labels
description: Ensures all required SDLC GitHub labels exist on the current repo. Creates any missing labels with correct descriptions; skips labels that already exist. Invoke this skill whenever the user asks to set up, initialize, or check GitHub labels for the project, mentions missing phase or type labels, or asks to ensure the repo is configured for the agentic SDLC workflow.
---

# ensure-github-labels

Ensure all required SDLC labels exist on the current GitHub repo. Create missing ones; skip existing ones.

## Required labels

| label | description |
|---|---|
| `feature` | New functionality |
| `bug` | Defect fixes |
| `chore` | Non-functional work: CI, dependencies, configuration, releases |
| `docs` | Documentation-only changes |
| `phase: triage` | Newly created, awaiting triage by Project Owner or in process of triage |
| `phase: spec` | Spec in progress or awaiting acceptance |
| `phase: tech-design` | Tech design in progress or awaiting acceptance |
| `phase: impl-plan` | Implementation plan in progress or awaiting acceptance |
| `phase: impl-coding` | Coding in progress; ends with code committed, pushed, and CI green on feature branch |
| `phase: impl-docs` | Documentation update in progress; ends with docs committed, pushed, and CI green on feature branch |
| `phase: impl-done` | Implementation and documentation complete, PR ready to be opened or open |
| `phase: merged` | Merged to main, pending release |
| `phase: released` | Included in a published release |

## Steps

1. Fetch existing labels from the repo (supports up to 200 existing labels):
   ```bash
   gh label list --limit 200 --json name
   ```

2. Parse the JSON to extract the list of existing label names.

3. For each label in the required table above, check if it already exists (case-sensitive match).

4. For each **missing** label, attempt to create it:
   ```bash
   gh label create "<name>" --description "<description>"
   ```
   If the command fails for any reason (e.g. the label was created concurrently, or already exists despite not appearing in the list), do not abort — record a warning for that label and continue with the rest.

5. Report results: list which labels were **created**, which were **already present** (skipped), and any **warnings** from failed create attempts.

## Output format

Print a summary like:

```
Created:
  ✓ phase: triage
  ✓ phase: spec

Already present (skipped):
  • feature
  • bug

Warnings:
  ⚠ chore — label create failed: already exists
```

If all labels already exist, say so and confirm no changes were made. Warnings are informational; the skill succeeds as long as all required labels are present after the run.
