---
name: sdlc-implement
description: Implements planned SDLC changes inside the story workspace folder outputs/<JIRA-KEY>/, with focused diffs, no secrets, and an implementation summary. Use for the implementation stage when coding from an implementation plan.
---

# SDLC implement

## Story workspace (required)

All code and stage artifacts for the story belong under:

`outputs/<JIRA-KEY>/`

Do **not** place application code in the pipeline repo root or under `src/sdlc_pipeline/`.

## Steps

1. Read `implementation-plan.md` and `design.md` inside the story folder.
2. Implement tasks in order **inside** `outputs/<JIRA-KEY>/` (create `src/`, apps, tests, config as needed).
3. Keep diffs focused; no unrelated refactors.
4. Never hardcode `.env` secrets into source.
5. Add/update tests when risk or plan requires it (also under the story folder).
6. Write `implementation.md` in the story folder summarizing changes and how to test.

## Checklist

- [ ] All code paths are under `outputs/<JIRA-KEY>/`
- [ ] Plan tasks covered or deviations noted
- [ ] No secrets in code or artifacts
- [ ] Local run/test steps documented (relative to the story folder)
