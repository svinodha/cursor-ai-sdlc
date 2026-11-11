# PR Creation — EPMCDMETST-68575

## Status

**Draft-only** — no GitHub PR URL was created.

Reasons:
- Working tree is on `main` with uncommitted story work; nothing was pushed for this story.
- `gh` CLI is not available in this environment (`gh` command not found).
- Repo `.gitignore` ignores `outputs/**` (except `outputs/.gitkeep`), so the story workspace would not enter a normal commit without an explicit exception or force-add.
- No force-push and no unsolicited commit were performed.

## PR title

```
EPMCDMETST-68575: Add manager leave-approval flow with optional comment and balance deduction
```

## Ready-to-submit PR body

```markdown
## Summary
- Managers can approve pending leave requests from the Manager Dashboard with an optional comment.
- Approval atomically moves status Pending → Approved, stores the comment, deducts leave balance, and removes the request from the pending list (CAS + lock guards double-submit).
- Employee leave history shows Approved status and any manager comment; manager receives a success toast.
- Self-contained demo lives under `outputs/EPMCDMETST-68575/` (Flask app + 36 automated tests). Verification: **pass**. Demo auth (`X-User-Id` / `X-Role`) is not production-safe.

## Jira
- EPMCDMETST-68575 — https://jiraeu.epam.com/browse/EPMCDMETST-68575

## Artifacts
All under `outputs/EPMCDMETST-68575/`:
- [requirement-analysis.md](./requirement-analysis.md)
- [architecture.md](./architecture.md)
- [design.md](./design.md)
- [design-review.md](./design-review.md)
- [implementation-plan.md](./implementation-plan.md)
- [implementation.md](./implementation.md)
- [code-review.md](./code-review.md)
- [verification.md](./verification.md)

## Test plan
- [x] From story folder: `PYTHONPATH=src` and `pytest tests -q` → **36 passed** (verification evidence)
- [ ] Manual: open `/manager`, Approve → optional comment dialog; submit empty and with comment
- [ ] Manual: confirm success toast, row leaves pending list, balance deducted
- [ ] Manual: Cancel/Esc dialog → no network write / no status change
- [ ] Manual: `/employee/history` shows Approved + manager comment
- [ ] Confirm no secrets/`.env` in the PR diff; exclude `.venv/`, `__pycache__/`, `.pytest_cache/`
```

## Branch notes

| Item | Value |
|------|--------|
| Suggested branch | `feature/EPMCDMETST-68575-leave-approval` |
| Base branch | `main` (`origin/main` @ `55e6667`) |
| Scope | Prefer `outputs/EPMCDMETST-68575/` only (artifacts + app + tests + story `README.md` / `requirements.txt`) |
| Exclude | `.venv/`, `__pycache__/`, `.pytest_cache/`, any `.env`, secrets |
| Gitignore note | Root `.gitignore` has `outputs/**`; allowlist this story path or `git add -f` the intended files before commit |
| Current HEAD | Local `main`, up to date with `origin/main`; story deliverables are untracked / ignored |

## PR URL

Not created.

## Exact next steps

1. Install/auth GitHub CLI if desired: [https://cli.github.com/](https://cli.github.com/) then `gh auth login`.
2. Create and switch to the suggested branch from repo root:
   ```powershell
   git checkout -b feature/EPMCDMETST-68575-leave-approval
   ```
3. Allowlist or force-add only the story deliverables (not `.venv`):
   ```powershell
   # Option A: temporary allowlist in .gitignore, e.g.
   #   !outputs/EPMCDMETST-68575/
   #   !outputs/EPMCDMETST-68575/**
   #   outputs/EPMCDMETST-68575/.venv/
   # then:
   git add outputs/EPMCDMETST-68575

   # Option B without editing ignore:
   git add -f outputs/EPMCDMETST-68575/requirement-analysis.md `
     outputs/EPMCDMETST-68575/architecture.md `
     outputs/EPMCDMETST-68575/design.md `
     outputs/EPMCDMETST-68575/design-review.md `
     outputs/EPMCDMETST-68575/implementation-plan.md `
     outputs/EPMCDMETST-68575/implementation.md `
     outputs/EPMCDMETST-68575/code-review.md `
     outputs/EPMCDMETST-68575/verification.md `
     outputs/EPMCDMETST-68575/pr-creation.md `
     outputs/EPMCDMETST-68575/jira-story.md `
     outputs/EPMCDMETST-68575/pipeline-state.json `
     outputs/EPMCDMETST-68575/README.md `
     outputs/EPMCDMETST-68575/requirements.txt `
     outputs/EPMCDMETST-68575/src `
     outputs/EPMCDMETST-68575/tests
   ```
4. Commit with a message focused on why (only when you intend to publish):
   ```powershell
   git commit -m "EPMCDMETST-68575: add manager leave-approval demo with atomic balance deduction"
   ```
5. Push (no force) and open the PR:
   ```powershell
   git push -u origin HEAD
   gh pr create --base main --title "EPMCDMETST-68575: Add manager leave-approval flow with optional comment and balance deduction" --body-file outputs/EPMCDMETST-68575/pr-creation.md
   ```
   Or paste the **Ready-to-submit PR body** section above into the GitHub UI.

## Secrets check

- No `.env` present under the story workspace.
- PR body contains no tokens, credentials, or `.env` contents.
- Demo auth is header-based and explicitly non-production.
