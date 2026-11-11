---
name: sdlc-technical-design
description: Produces detailed technical design—APIs, data models, edge cases, and security notes—ready for implementation planning. Use for the design stage after architecture is available.
---

# SDLC technical design

## Steps

1. Read requirements + architecture artifacts in `outputs/<JIRA-KEY>/`.
2. Convert architecture into concrete module/API/data decisions for code that will live in that folder.
3. Specify validation, errors, edge cases, migrations/compatibility.
4. Note testability and rollout/feature-flag needs.
5. Stay within story scope; do not implement code yet.

## Output template

```markdown
# Design — <STORY-KEY>

## Design overview
## Module design
## APIs and interfaces
## Data models
## Error handling and edge cases
## Security and privacy
## Testability and rollout
## Open questions
```
