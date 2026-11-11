# Implementation Plan — EPMCDMETST-68575

## Summary

Build a self-contained leave-approval feature slice under `outputs/EPMCDMETST-68575/src/` per [design.md](./design.md), honoring [design-review.md](./design-review.md) **conditional-go** items. Work is sequenced domain → stores/UoW (with CAS) → services → API → UI → wiring/seed → tests. No reject/bulk/notification scope. Do not start coding outside this plan’s touchpoints; all application code stays in this story folder.

### Design defaults — accepted for workspace demo

Per design-review major finding: **accept** these defaults; do not change mid-implementation without product override:

| Topic | Accepted default |
|-------|------------------|
| Insufficient balance | **Block** approval (`409 insufficient_balance`); no status/balance change |
| Comment max length | **500** chars; trim; empty/whitespace → `null` |
| Approver scope | Authenticated **manager** with `request.manager_id == actor.user_id` |
| Leave units | Deduct `request.duration_days` (decimal days) for `request.leave_type` |
| Success UX | Close dialog → toast “Leave request approved.” → remove pending row |
| API | Greenfield approve + read queries in this workspace |

### Conditional-go constraints (must implement)

1. **CAS / concurrency:** In-memory approve path must reload-or-CAS **inside** the UoW under a store lock (version or status check). Concurrent/double submit → one success, second `not_pending`, **single** balance deduction.
2. **Demo-only auth:** `X-User-Id` / `X-Role` headers are **demo-only**; document that production must replace with real session/auth. Do not treat header trust as production-safe.
3. **UI stack choice:** Server-rendered HTML templates + light vanilla JS (dialog open/close, in-flight disable, toast, fetch approve). Simplest path for AC-01/02/06/08/10 without HTMX/SPA thrash.
4. **Error UX:** On `400`/`409` keep dialog open with inline/toast error; close dialog + success toast **only** on `200`.
5. **Duration guard:** Reject `duration_days <= 0` (or missing) at approve with domain/API validation error; seed data always uses positive duration.
6. **History demo:** Seed a distinct employee actor; history query scoped to acting user only (IDOR rule).

## Tasks

| # | Task | Outcome | Depends on |
|---|------|---------|------------|
| 1 | Scaffold package layout under `src/leave_approval/` (`models`, `errors`, `auth`, package `__init__`) | Importable package with `LeaveStatus`, `LeaveRequest`, `LeaveBalance`, `ActingUser`, typed domain errors | — |
| 2 | Implement in-memory stores + **locking CAS UoW** | `LeaveRequestStore` / `LeaveBalanceStore` protocols + in-memory impl; `UnitOfWork` that holds a mutex, reloads request inside transaction, compare-and-set on `status` (or version); commit/rollback semantics for approve writes | 1 |
| 3 | Implement `ApproveLeaveRequest` use case | Pending→Approved + optional comment + balance deduct in one UoW; authz (`manager` + `manager_id`); comment normalize (≤500); insufficient balance block; non-pending → `not_pending` no writes; reject `duration_days <= 0` | 2 |
| 4 | Implement query services | `list_pending_for_manager` (Pending only); `leave_history_for_employee` (status + `manager_comment`); IDOR-safe (actor id only) | 2 |
| 5 | Implement API schemas + routes | `POST .../approve`, `GET .../pending-leave-requests`, `GET .../leave-history`; map domain errors to HTTP codes from design; demo header auth explicitly labeled non-production | 3, 4 |
| 6 | Implement shared UI helpers | Dialog, toast, HTML-encode for comment render (XSS-safe), list row helpers | 1 |
| 7 | Implement Manager Dashboard UI | Pending list + Approve per row; optional-comment dialog; dismiss = no API (AC-10); in-flight disable; success toast + row removal; keep dialog open on 400/409 with error message | 5, 6 |
| 8 | Implement Employee History UI | Read-only history with Approved status + manager comment; distinct seeded employee actor for demo | 5, 6 |
| 9 | Wire `app.py` + seed data + README note | App factory wires stores/services/routes; seed pending requests, balances, manager + **distinct** employee; README/docstring: demo auth headers are not production | 5, 7, 8 |
| 10 | Unit/integration tests for domain + API | Cover happy path (with/without comment), not-pending, insufficient balance, invalid duration, authz failures, **concurrent/double submit → single deduction** | 3, 5 |
| 11 | Manual verification checklist pass | Walk AC-01–AC-10 against local app; record readiness for verify stage | 9, 10 |

## Touchpoints

All paths relative to `outputs/EPMCDMETST-68575/`:

| Path | Role |
|------|------|
| `src/leave_approval/__init__.py` | Package export |
| `src/leave_approval/models.py` | Entities, enums, DTOs (`PendingRow`, `HistoryRow`, `ApproveResult`) |
| `src/leave_approval/errors.py` | Domain errors (`NotPending`, `InsufficientBalance`, `Forbidden`, `NotFound`, `ValidationError`, …) |
| `src/leave_approval/auth.py` | `ActingUser`; demo header parsing (**demo-only**) |
| `src/leave_approval/stores.py` | Store protocols + in-memory impl with lock/version for CAS |
| `src/leave_approval/unit_of_work.py` | Transactional boundary; reload + status CAS inside lock |
| `src/leave_approval/services/approve_leave.py` | Approve use case |
| `src/leave_approval/services/queries.py` | Pending + history queries |
| `src/leave_approval/api/schemas.py` | Request/response validation (comment ≤500) |
| `src/leave_approval/api/routes.py` | HTTP handlers |
| `src/leave_approval/web/shared_ui.py` | Dialog, toast, encode-on-render |
| `src/leave_approval/web/manager_dashboard.py` | Dashboard templates/handlers + light JS |
| `src/leave_approval/web/employee_history.py` | History view |
| `src/leave_approval/web/templates/` *(as needed)* | HTML templates for dashboard/history/dialog |
| `src/leave_approval/web/static/` *(as needed)* | Minimal JS/CSS for dialog/toast/in-flight |
| `src/leave_approval/app.py` | Wiring + seed fixtures |
| `data/` *(optional)* | JSON file-backed demo persistence — no secrets |
| `tests/` | Domain + API + concurrency tests |
| `README.md` *(story folder)* | Run instructions; **demo auth is not production** |

Do **not** modify `src/sdlc_pipeline/`, `agents/`, or `.cursor/` for this story.

## Verification checkpoints

| Checkpoint | When | How | Pass criteria |
|------------|------|-----|---------------|
| VC-1 Domain approve happy path | After task 3 | Unit: approve with comment / without comment | Status `Approved`; comment saved or `null`; balance −`duration_days` |
| VC-2 Non-pending / insufficient / invalid duration | After task 3 | Unit | `not_pending` / `insufficient_balance` / validation; **no** balance change when rejected |
| VC-3 Concurrency / double submit | After task 2–3 | Unit or threaded test against in-memory store | One success; second `not_pending`; balance deducted **once** |
| VC-4 Authz + IDOR | After task 4–5 | API tests | Non-manager / wrong `manager_id` → 403; history only for acting employee |
| VC-5 API contract | After task 5 | Integration | 200 payload matches design; 400/401/403/404/409 codes as specified |
| VC-6 Dashboard UX | After task 7 | Manual | Approve opens dialog; cancel no change; success toast + row gone; error keeps dialog |
| VC-7 Employee history | After task 8 | Manual | Distinct employee sees Approved + comment |
| VC-8 AC traceability | After task 11 | Manual matrix AC-01–AC-10 | All story ACs demonstrable locally |

## Risks / rollback

| Risk | Mitigation | Rollback |
|------|------------|----------|
| In-memory race still allows double deduct | Mandatory store lock + reload/CAS inside UoW; VC-3 test | Fix store/UoW before shipping UI; do not weaken status check |
| Product rejects balance-block / 500-char / manager_id scope defaults | Defaults recorded above; change only via explicit product override + plan update | Revert behavior to prior accepted default in one place (use case + schema) |
| Demo header auth mistaken for production | README + auth module comments: **demo-only** | Replace auth adapter later; domain stays unchanged |
| XSS via manager comment | Validate length; store plain text; HTML-encode on render | Encode-on-render is mandatory; strip unsafe paths from templates |
| Scope creep (reject/bulk/email) | Out of scope per requirements | Do not implement; open follow-up story if needed |

**Rollback stance:** Feature is isolated under this story folder; discard or revert story `src/` / `tests/` / optional `data/` without touching the pipeline framework.
