---
name: sdlc-design-review
description: Critiques a technical design against requirements using a severity rubric and go/conditional-go/no-go recommendation. Use for design-review stage or when validating a design before planning.
---

# SDLC design review

## Severity

- **blocker** — must resolve before planning/implementation
- **major** — should resolve or explicitly accept risk
- **minor** — improvement, non-blocking

## Steps

1. Trace design back to acceptance criteria and architecture.
2. Hunt gaps, contradictions, over-engineering, missing edge cases.
3. Assess security, operability, testability.
4. Recommend alternatives only when materially better.
5. End with **go** / **conditional-go** / **no-go**.

## Output template

```markdown
# Design Review — <STORY-KEY>

## Summary
## Findings
| Severity | Issue | Recommendation |
|----------|-------|----------------|
## Requirement coverage
## Residual risks
## Recommendation
```
