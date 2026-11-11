# Implementation — EPMCDMETST-68575

## Summary

Implemented a self-contained Manager Dashboard leave-approval demo under `outputs/EPMCDMETST-68575/` per [implementation-plan.md](./implementation-plan.md) and [design.md](./design.md). Managers can approve a pending request with an optional comment; the server atomically sets status to Approved, stores the comment, and deducts leave balance. Employee history shows Approved status and manager comment. Concurrent/double submit is guarded with a store lock + version/status CAS (single deduction).

## Files touched

All paths relative to `outputs/EPMCDMETST-68575/`:

| Path | Role |
|------|------|
| `src/leave_approval/__init__.py` | Package export |
| `src/leave_approval/models.py` | Entities, enums, DTOs |
| `src/leave_approval/errors.py` | Domain errors |
| `src/leave_approval/auth.py` | ActingUser + **demo-only** header parsing |
| `src/leave_approval/stores.py` | In-memory stores + CAS |
| `src/leave_approval/unit_of_work.py` | Locked UoW with reload + status/version CAS |
| `src/leave_approval/services/approve_leave.py` | Approve use case |
| `src/leave_approval/services/queries.py` | Pending + history queries (IDOR-safe) |
| `src/leave_approval/api/schemas.py` | Request/response helpers |
| `src/leave_approval/api/routes.py` | Flask API routes |
| `src/leave_approval/web/shared_ui.py` | HTML-encode, badges |
| `src/leave_approval/web/manager_dashboard.py` | Dashboard page |
| `src/leave_approval/web/employee_history.py` | History page |
| `src/leave_approval/web/templates/*.html` | Server-rendered UI |
| `src/leave_approval/web/static/app.js` | Dialog, toast, in-flight, fetch approve |
| `src/leave_approval/web/static/app.css` | Minimal styles |
| `src/leave_approval/app.py` | App factory + seed data |
| `tests/` | Domain, API, query, UI helper, concurrency tests |
| `requirements.txt` | flask, pytest |
| `README.md` | Run instructions; demo auth warning |

Pipeline framework (`src/sdlc_pipeline/`, `agents/`, `.cursor/`) was **not** modified.

## How to run

From the story folder:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONPATH="src"
python -m leave_approval.app
```

- Manager Dashboard: http://127.0.0.1:5055/manager (actor `mgr-1`)
- Employee History: http://127.0.0.1:5055/employee/history (actor `emp-1`)

**Demo auth:** `X-User-Id` / `X-Role` headers are **not production-safe**.

## How to test

```bash
cd outputs/EPMCDMETST-68575
$env:PYTHONPATH="src"
.\.venv\Scripts\python -m pytest tests -v
```

Result at implementation time: **36 passed**.

Coverage includes: approve with/without comment, not-pending, insufficient balance, invalid duration, authz failures, concurrent double-submit → single deduction, pending/history IDOR scoping, API status codes, XSS encode-on-render.

## Plan coverage / deviations

| Plan task | Status |
|-----------|--------|
| 1 Scaffold package | Done |
| 2 Stores + locking CAS UoW | Done (`version` + `status` CAS under mutex) |
| 3 ApproveLeaveRequest | Done |
| 4 Query services | Done |
| 5 API schemas + routes | Done (Flask) |
| 6 Shared UI helpers | Done |
| 7 Manager Dashboard UI | Done (templates + vanilla JS) |
| 8 Employee History UI | Done (distinct `emp-1` seed) |
| 9 app.py + seed + README | Done |
| 10 Unit/integration tests | Done (36 tests) |
| 11 Manual AC checklist | Ready for verify stage — exercise `/manager` + `/employee/history` locally |

**Deviations:**

1. Used **Flask** for HTTP/templates (design allowed Flask/FastAPI-style). No HTMX/SPA.
2. Optional JSON file-backed `data/` store was **not** added; in-memory seed is sufficient for demo/tests.
3. UI pages default actor via query/default id (`mgr-1` / `emp-1`); API still requires demo headers.

Accepted design defaults implemented unchanged: block on insufficient balance; comment max 500; manager_id scope; deduct `duration_days`; success toast + row removal; keep dialog open on 400/409.

## Manual verification readiness (AC-01–AC-10)

| AC | Demonstrable via |
|----|------------------|
| AC-01 Approve control | `/manager` pending rows |
| AC-02 Optional comment dialog | Approve → dialog |
| AC-03 Pending → Approved | Approve API / domain |
| AC-04 Comment saved | Approve with comment → history |
| AC-05 Balance deduct | `balance_after` in API; store |
| AC-06 Removed from pending | UI row drop + pending query |
| AC-07 Employee history | `/employee/history` as `emp-1` |
| AC-08 Success toast | UI on 200 |
| AC-09 Non-pending safe | 409 + concurrency test |
| AC-10 Dialog dismiss no writes | Cancel/Esc — no fetch |
