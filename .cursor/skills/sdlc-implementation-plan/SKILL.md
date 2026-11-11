---
name: sdlc-implementation-plan
description: Breaks a reviewed design into an ordered implementation plan with touchpoints, dependencies, and verification checkpoints. Use for implementation-plan stage before coding.
---

# SDLC implementation plan

## Steps

1. Read `design.md` and `design-review.md` (honor blockers / conditional-go items).
2. Sequence tasks with clear outcomes; note dependencies.
3. List likely files/modules **under** `outputs/<JIRA-KEY>/` only.
4. Add verification checkpoints (unit/integration/manual).
5. Keep plan sized to the story; do not start coding.

## Output template

```markdown
# Implementation Plan — <STORY-KEY>

## Summary
## Tasks
| # | Task | Outcome | Depends on |
|---|------|---------|------------|
## Touchpoints
## Verification checkpoints
## Risks / rollback
```
