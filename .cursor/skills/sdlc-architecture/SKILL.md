---
name: sdlc-architecture
description: Produces a high-level architecture proposal from requirements—components, data flow, integrations, and NFR trade-offs. Use for the architecture stage or system-structure decisions before detailed design.
---

# SDLC architecture

## Steps

1. Read `jira-story.md` and `requirement-analysis.md`.
2. Identify affected boundaries, components, and integrations **to be built inside** `outputs/<JIRA-KEY>/`.
3. Prefer the simplest architecture that meets acceptance criteria.
4. Cover security, performance, reliability, observability only at high level.
5. Leave API contracts and code-level detail to the design stage.

## Output template

```markdown
# Architecture — <STORY-KEY>

## Context and drivers
## Proposed overview
## Components and responsibilities
| Component | Responsibility |
|-----------|----------------|
## Data flow
## Integration points
## NFR considerations
## Trade-offs
```
