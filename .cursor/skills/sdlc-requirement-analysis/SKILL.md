---
name: sdlc-requirement-analysis
description: Turns a Jira story into a testable requirements brief with scope, acceptance criteria, and clarifying questions when anything is unclear. Use for requirement analysis stage or when clarifying story scope before design.
---

# SDLC requirement analysis

## Steps

1. Read `jira-story.md` fully.
2. Restate problem and outcome without inventing contradictory requirements.
3. Split **in scope** vs **out of scope**.
4. List acceptance criteria; tag inferred items as `(inferred)`.
5. **Ask clarifying questions** whenever the story is unclear, incomplete, contradictory, or missing edge-case behavior that would change design/implementation.
6. Capture assumptions, dependencies, risks, and open questions.
7. If answers are unavailable in this run, document blocking questions and tag temporary assumptions as `(assumption — pending answer)`.

## When to ask

Ask (do not guess) for things like:

- Missing actors, permissions, or systems of record
- Ambiguous status transitions or side effects (e.g. balance rules)
- Unspecified error/empty states that affect acceptance
- Conflicting acceptance criteria
- Scope boundaries that would change effort materially

## Output template

```markdown
# Requirement Analysis — <STORY-KEY>

## Problem statement
## Goals
## Non-goals
## Scope
### In scope
### Out of scope
## Acceptance criteria
| ID | Criterion | Source |
|----|-----------|--------|
## Clarifying questions
1. ...
## Assumptions
## Dependencies
## Risks
## Open questions
```
