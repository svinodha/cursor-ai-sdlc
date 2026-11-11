# Code Review — EPMCDMETST-68575

## Summary

Reviewed implementation under `outputs/EPMCDMETST-68575/` against [requirement-analysis.md](./requirement-analysis.md), [design.md](./design.md), and [implementation.md](./implementation.md). Domain approve path, API mapping, pending/history queries, HTML encode-on-render, and in-memory CAS concurrency match the design defaults (block insufficient balance, comment max 500, manager_id scope, single deduction). **36/36** tests passed locally. Demo auth is clearly labeled and contains no secrets. No blockers found; remaining items are suggestions or nits that can be handled in verify/manual checks or before any non-demo deployment.

## Findings

| Severity | Location | Issue | Recommendation |
|----------|----------|-------|----------------|
| suggestion | `web/manager_dashboard.py`, `web/employee_history.py` | HTML pages build `ActingUser` from `?as=` / default ids and bypass API header auth. Fine for local demo, but page-layer identity is spoofable (including history via `?as=`). | Keep demo-only; before production replace with real session auth and remove query-param impersonation. |
| suggestion | `app.py` `main()` | `app.run(..., debug=True)` enables the interactive debugger on unexpected errors. Bound to `127.0.0.1`, but risky if host/port change. | Use `debug=False` by default; opt in via env flag for local development only. |
| suggestion | `api/routes.py` | Non-`DomainError` exceptions are not mapped to design’s structured `500` / `internal_error` JSON body (Flask default error page). | Add a narrow Flask error handler that returns `{"code":"internal_error",...}` without stack traces. |
| suggestion | `tests/test_api.py` `test_history_idor_scoped_to_actor` | Assertion `assert all(True for _ in items)` is a no-op; IDOR intent relies on sibling id checks only. | Assert every item belongs to the actor (e.g. store round-trip or employee-scoped fields) so the test fails if scoping regresses. |
| suggestion | `web/static/app.js`, UI flows AC-02/08/10 | Dialog dismiss / toast / in-flight behavior is implemented in JS but not covered by automated browser tests. | Cover in verify-stage manual checklist (Cancel/Esc → no network; success toast + row removal). |
| nit | `web/templates/base.html` | Demo banner says auth via “cookies” while the app uses `X-User-Id` / `X-Role` headers. | Rephrase banner to “headers” for accuracy. |
| nit | `unit_of_work.py` `commit` | CAS failure when the request is missing returns `NotPending` rather than `NotFound`. | Map missing entity after CAS to `NotFound` if product cares about the distinction. |
| nit | `api/schemas.py` | `float(duration_days)` / `float(balance_after)` can lose Decimal precision for exotic fractions. | Acceptable for demo day counts; keep Decimal (or string) if integrating with real payroll math. |

## Test coverage

| Area | Evidence |
|------|----------|
| Approve + comment / empty comment | `test_approve_leave.py`, `test_api.py` |
| Non-pending / insufficient balance / invalid duration | Domain + API tests |
| Authz (401/403) + not found | API tests |
| Concurrent double-submit → single deduction | `test_concurrent_double_submit_single_deduction` |
| Pending scope + history IDOR (API/service) | `test_queries.py`, `test_api.py` |
| XSS encode on history render | `test_html_encode_comment_in_history`, `test_shared_ui.py` |
| Dashboard/history HTML smoke | `test_manager_dashboard_renders`, `test_employee_history_page_renders` |
| Gaps | No automated UI tests for dialog cancel (AC-10), toast (AC-08), or in-flight double-click; rely on manual verify |

Local run: `pytest tests -v` → **36 passed**.

## Required fixes

None (blocker count: **0**).

## Suggestions

1. Treat header/`?as=` identity as demo-only; do not promote this package to shared environments without real auth.
2. Prefer `debug=False` by default and structured `internal_error` JSON for unexpected failures.
3. Strengthen the history IDOR API test and exercise AC-02/08/10 manually in verification.
4. Fix the base template “cookies” wording nit when convenient.

## Recommendation

**Go** — implementation is ready for the verification stage. **0 blockers.** Address suggestions before any production-oriented reuse; they do not block AC verification of this workspace demo.
