---
name: sdlc-create-pr
description: Drafts and creates the closing pull request for an SDLC pipeline run, linking Jira and stage artifacts without secrets. Use for pr-creation stage or finalizing pipeline delivery.
---

# SDLC create PR

## Steps

1. Treat `outputs/<STORY-KEY>/` as the deliverable workspace (artifacts + code).
2. Read prior artifacts there, especially `verification.md`.
3. Draft title + body focused on **why**; scope the PR to that story folder when possible.
4. Link Jira story and stage artifacts.
5. Include a short test plan from verification evidence.
6. Prefer `gh pr create` against the configured GitHub remote. Auth via `GITHUB_TOKEN` or `GH_TOKEN` from `.env` (never print the token).
7. Create the PR when remotes/permissions allow; otherwise leave a ready body and exact next steps.
8. No force-push; never include secrets/`.env` in the PR.

## PR body skeleton

```markdown
## Summary
- ...

## Jira
- <STORY-KEY> — <url>

## Artifacts
- requirement-analysis.md … verification.md

## Test plan
- [ ] ...
```
