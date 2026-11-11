# Design — EPMCDMETST-68575

## Design overview

Concrete design for the Manager Dashboard leave-approval slice scoped to [requirement-analysis.md](./requirement-analysis.md) and [architecture.md](./architecture.md). All application code will live under `outputs/EPMCDMETST-68575/src/`.

**Intent:** A manager approves one pending leave request with an optional comment. The server atomically transitions status `Pending` → `Approved`, persists the comment, deducts leave balance for the request’s leave type/duration, and returns a result the dashboard uses for success confirmation and pending-list removal. Employee history reads status + manager comment.

**Implementation stance (workspace greenfield):** Build a self-contained Python package under `src/` with an in-memory / file-backed store suitable for local demo and tests. Domain rules live in a single approve use case; UI and API stay thin. No reject/bulk/notification features.

**Resolved defaults for open product questions** (marked `(design default)` — override if product clarifies):

| Question | Design default |
|----------|----------------|
| Insufficient balance | **Block** approval with a clear error; no status/balance change. |
| Comment max length | **500** characters; trim whitespace; empty/whitespace → `null`. |
| Who may approve | Any authenticated **manager** with the request in their pending scope (manager id matches request’s `manager_id`). |
| Success UX | Close dialog → **toast** “Leave request approved.” → remove row from pending list. |
| Leave units | Deduct `request.duration_days` (decimal days) from balance for `request.leave_type`; no holiday/proration logic in this story. |
| Existing API | **Greenfield** approve command + read queries in this workspace. |

## Module design

```text
outputs/EPMCDMETST-68575/
  src/
    leave_approval/
      __init__.py
      models.py              # Domain entities / enums / DTOs
      errors.py              # Typed domain errors
      auth.py                # Acting user context (manager/employee)
      stores.py              # LeaveRequestStore, LeaveBalanceStore protocols + in-memory impl
      unit_of_work.py        # Transactional boundary for approve
      services/
        approve_leave.py     # ApproveLeaveRequest use case (AC-03–05, AC-09)
        queries.py           # Pending list + employee history queries
      api/
        routes.py            # HTTP handlers (or Flask/FastAPI-style functions)
        schemas.py           # Request/response validation schemas
      web/
        manager_dashboard.py # Pending list, Approve, comment dialog, toast (AC-01,02,06,08,10)
        employee_history.py  # History list with status + comment (AC-07)
        shared_ui.py         # Dialog, toast, list row helpers
      app.py                 # Wire stores, services, routes; seed demo data
  tests/                     # Planned in later stages; design notes test seams below
```

| Module | Responsibility | AC mapping |
|--------|----------------|------------|
| `web/manager_dashboard` | Render pending rows; Approve per row; open/dismiss optional-comment dialog; call approve API; toast on success; drop row locally | AC-01, AC-02, AC-06, AC-08, AC-10 |
| `web/employee_history` | Read-only history for employee; show status + manager comment | AC-07 |
| `web/shared_ui` | Dialog, toast/banner, pending/history row presentation | Shared |
| `api/routes` + `schemas` | Validate payloads; map auth + use-case results to HTTP | All write/read paths |
| `services/approve_leave` | Single-transition approve + comment + balance deduct in one UoW | AC-03–05, AC-09 |
| `services/queries` | Pending-for-manager; history-for-employee | AC-01, AC-06, AC-07 |
| `stores` + `unit_of_work` | Persist requests/balances; atomic commit/rollback | Reliability |

UI may be server-rendered templates or a thin JS/HTMX layer; either is fine if behavior matches the flows below. Prefer keeping view logic in `web/` and HTTP in `api/`.

## APIs and interfaces

### Auth context

```text
ActingUser { user_id: str, role: "manager" | "employee" }
```

Injected from session/header in local app (e.g. `X-User-Id` + `X-Role` for demo). Production would use real auth; no secrets in code.

### Commands

#### `POST /api/leave-requests/{request_id}/approve`

**Caller:** Manager Dashboard after comment dialog submit.

**Auth:** `role == manager`.

**Body:**

```json
{
  "comment": "string | null"   // optional; omit, null, or "" => no comment
}
```

**Validation (API layer):**

- `request_id`: non-empty string / UUID format as used by store.
- `comment`: optional string; if present, length ≤ 500 after trim; reject 400 if over max.

**Success `200`:**

```json
{
  "request_id": "...",
  "status": "Approved",
  "manager_comment": "text or null",
  "balance_after": 12.0,
  "message": "Leave request approved."
}
```

**Errors:**

| HTTP | Code | When |
|------|------|------|
| 401 | `unauthorized` | Missing/invalid acting user |
| 403 | `forbidden` | Not a manager, or request not in this manager’s scope |
| 404 | `not_found` | Unknown `request_id` |
| 409 | `not_pending` | Status ≠ Pending (AC-09; no balance change) |
| 409 | `insufficient_balance` | Balance &lt; duration `(design default)` |
| 400 | `validation_error` | Comment too long / bad body |
| 500 | `internal_error` | Unexpected failure after rollback |

### Queries

#### `GET /api/managers/me/pending-leave-requests`

**Auth:** manager.  
**Response:** list of pending requests for `manager_id == acting user` (fields needed for dashboard rows). Approved items must not appear (AC-06).

#### `GET /api/employees/me/leave-history`

**Auth:** employee (or manager viewing self as employee in demo).  
**Response:** leave requests for that employee including `status` and `manager_comment` (AC-07).

### Domain interfaces

```text
ApproveLeaveRequest.execute(actor: ActingUser, request_id: str, comment: str | None)
  -> ApproveResult

LeaveRequestStore.get(id) / save(entity) / list_pending_for_manager(manager_id)
LeaveBalanceStore.get(employee_id, leave_type) / save(balance)
UnitOfWork.run(fn)  # commit on success; rollback on error
```

Approve sequence (server):

1. Authorize manager + load request; 404/403 as above.
2. If `status != Pending` → raise `not_pending` (no writes).
3. Normalize comment (`trim`; empty → `null`; enforce max length).
4. Load balance for `(employee_id, leave_type)`; if `balance.days < request.duration_days` → `insufficient_balance`.
5. In one UoW: set `status=Approved`, set `manager_comment`, set `approved_at`, `approved_by`; decrement balance by `duration_days`.
6. Return `ApproveResult` for API mapping.

### UI flows

1. **Approve (happy path):** Approve click → dialog open (comment optional) → Confirm → `POST approve` → toast success → remove row (AC-01,02,03,04,05,06,08).
2. **Dismiss dialog:** Cancel/Esc/overlay → no API call; list unchanged (AC-10).
3. **In-flight guard:** Disable Confirm + Approve controls while request pending; ignore double-clicks.
4. **Employee history:** Load history query; show status badge and manager comment when present (AC-07).

## Data models

### Enums

- `LeaveStatus`: `Pending` | `Approved` (other values may exist in store for AC-09 tests, e.g. `Cancelled`, but this story only transitions Pending→Approved).
- `LeaveType`: string enum or constrained string, e.g. `Annual`, `Sick`, `Personal` (demo set).

### `LeaveRequest`

| Field | Type | Notes |
|-------|------|-------|
| `id` | str | Primary key |
| `employee_id` | str | Requester |
| `manager_id` | str | Approver scope |
| `leave_type` | str | Balance key |
| `duration_days` | Decimal | Units deducted on approve |
| `start_date` / `end_date` | date | Display on UI |
| `status` | LeaveStatus | Pending → Approved |
| `manager_comment` | str \| null | Optional; set only on approve |
| `created_at` | datetime | |
| `approved_at` | datetime \| null | Set on approve |
| `approved_by` | str \| null | Manager user id |

### `LeaveBalance`

| Field | Type | Notes |
|-------|------|-------|
| `employee_id` | str | |
| `leave_type` | str | |
| `days_remaining` | Decimal | Decremented by `duration_days` |

### Read DTOs

- **PendingRow:** id, employee display name/id, leave_type, dates, duration_days, status (always Pending in this list).
- **HistoryRow:** id, leave_type, dates, duration_days, status, manager_comment.

### Persistence

- Protocol-based stores with an **in-memory** implementation for the story workspace (optionally JSON file under `outputs/EPMCDMETST-68575/data/` for demo persistence — no secrets).
- No schema migration tooling required for in-memory/demo store; if a file store is used, version a simple `schema_version` field for forward compatibility.
- Compatibility: approving never mutates historical fields other than status/comment/approval metadata/balance.

## Error handling and edge cases

| Case | Behavior |
|------|----------|
| Dialog cancel / dismiss | No API call; no state change (AC-10). |
| Empty / whitespace comment | Stored as `null`; approval still succeeds (AC-02, AC-04). |
| Comment &gt; 500 chars | 400 validation; no approve. |
| Already Approved / non-Pending | 409 `not_pending`; balance unchanged (AC-09). |
| Unknown request | 404. |
| Manager not owner of request | 403. |
| Non-manager caller | 403. |
| Insufficient balance | 409 `insufficient_balance`; no status change `(design default)`. |
| Concurrent double approve | UoW + status check: second call gets `not_pending`; at most one deduction. Prefer compare-and-set / reload-inside-transaction. |
| Network / 5xx after submit | Keep row; show error toast; allow retry; server remains idempotent if first call actually committed (second → `not_pending`). |
| Missing balance row | Treat as 0 remaining → insufficient (or create with 0); do not invent unlimited balance. |

Client error display: map API `code` to short messages (e.g. “This request is no longer pending.”, “Insufficient leave balance.”). Do not show stack traces.

## Security and privacy

- Authorize every approve against acting manager role **and** `request.manager_id == actor.user_id`.
- Treat `manager_comment` as untrusted input: validate length; store as plain text; **HTML-encode** on render (dashboard toast/history) to mitigate XSS.
- Do not log full comment bodies in info logs if avoidable; log `request_id`, `actor_id`, outcome code only.
- No credentials, tokens, or `.env` values in `src/` or stage Markdown. Demo auth headers are non-secret identifiers only.
- Employee history returns only the acting employee’s requests (IDOR: never accept arbitrary `employee_id` from client without auth check).

## Testability and rollout

### Test seams

- Inject `LeaveRequestStore`, `LeaveBalanceStore`, and `UnitOfWork` (or clock) into `ApproveLeaveRequest`.
- Pure domain tests: Pending→Approved + deduction; not-pending no-op; insufficient balance; comment normalization; authorization failures.
- API tests: status codes/payloads for success and each error code.
- UI behavior tests (later): Approve opens dialog; dismiss no call; success removes row and shows toast.

### Suggested test matrix (for implementation/verify stages)

| Scenario | Expect |
|----------|--------|
| Approve with comment | Status Approved; comment saved; balance −duration; removed from pending |
| Approve without comment | `manager_comment is null`; still Approved |
| Approve non-pending | 409; balance unchanged |
| Double submit | One success; second 409; single deduction |
| Insufficient balance | 409; still Pending |
| Dialog cancel | No API; still Pending |

### Rollout

- No feature flag required for this workspace demo app; ship as the approve path of the local feature slice.
- If later integrated into a larger product: gate with `leave_approval_v1` flag default off; enable for manager cohort after verify.
- Seed data script/fixture in `app.py` for manual demo (sample pending requests + balances) — no production data.

## Open questions

1. Confirm product preference if **insufficient balance** should allow negative balances instead of blocking `(design default: block)`.
2. Confirm **comment max length** (500) and whether markdown/plain-text-only is required.
3. Confirm **direct-manager-only** vs broader org-manager access if dashboard scope differs from `manager_id` on the request.
4. Confirm leave duration field: days vs hours — design uses `duration_days` only.
5. If this slice must later plug into an existing corporate API, replace in-memory stores with adapters; domain use case should stay unchanged.
