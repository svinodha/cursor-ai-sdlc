---
name: sdlc-code-review
description: Reviews SDLC implementation for correctness, security, and maintainability with blocker vs suggestion findings. Use for code-review stage or reviewing pipeline-produced diffs.
---

# SDLC code review

## Severity

- **blocker** — must fix before verification/PR
- **suggestion** — optional improvement
- **nit** — style-only, low priority

## Focus

1. Review code under `outputs/<JIRA-KEY>/` only (story workspace)
2. Correctness vs requirements/design
3. Edge cases and error handling
4. Security (injection, authz, secret leakage, unsafe defaults)
5. Tests adequacy
6. Avoid large unrelated rewrites unless fixing a blocker

## Output template

```markdown
# Code Review — <STORY-KEY>

## Summary
## Findings
| Severity | Location | Issue | Recommendation |
|----------|----------|-------|----------------|
## Test coverage
## Required fixes
## Suggestions
## Recommendation
```
