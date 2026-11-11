---
name: sdlc-verify
description: Verifies implementation against acceptance criteria with a traceability matrix and recorded test evidence. Use for verification stage before PR creation.
---

# SDLC verify

## Steps

1. Read `requirement-analysis.md`, `implementation.md`, `code-review.md` in `outputs/<JIRA-KEY>/`.
2. Map each acceptance criterion to evidence from code/tests in that same folder.
3. Run relevant automated tests when possible (from the story folder); record commands + results.
4. Confirm blockers from code review are resolved or explicitly waived.
5. Do not create the PR in this stage.

## Output template

```markdown
# Verification — <STORY-KEY>

## Summary
## Traceability
| AC ID | Criterion | Evidence | Status |
|-------|-----------|----------|--------|
## Checks executed
## Gaps / residual risks
## Recommendation (pass/fail)
```
