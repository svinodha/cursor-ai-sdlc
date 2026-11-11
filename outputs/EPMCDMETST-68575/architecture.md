# Architecture — EPMCDMETST-68575

## Context and drivers

- **Story:** [Manager Dashboard - Approving Leave Request](https://jiraeu.epam.com/browse/EPMCDMETST-68575) ([jira-story.md](./jira-story.md)).
- **Requirements:** [requirement-analysis.md](./requirement-analysis.md) — managers approve pending leave with an optional comment; status becomes Approved; leave balance is deducted; pending list and employee history update; manager sees success confirmation (AC-01–AC-08), with safe no-op on cancel and idempotent failure if not Pending (AC-09–AC-10).
- **Workspace constraint:** All application code and stage artifacts for this story live under `outputs/EPMCDMETST-68575/` (prefer `src/`). This proposal targets a self-contained leave-approval feature slice in that folder.
- **Drivers:** Correct single-request approval path; atomic status + balance update; optional comment persistence; clear manager UX; simplest structure that meets acceptance criteria without reject/bulk/notification scope.

## Proposed overview

A small layered app inside the story workspace:

1. **Manager Dashboard UI** — lists pending requests, Approve control, optional-comment dialog, success confirmation, and list refresh.
2. **Employee History UI** — read-only view of request status and manager comment.
3. **Leave Approval API** — single command endpoint that validates Pending → Approved, saves optional comment, deducts balance, and returns success/error.
4. **Domain + persistence** — leave request and leave balance stores with a transactional approve operation to avoid double deduction.

```text
[Manager Dashboard UI] --approve(+optional comment)--> [Leave Approval API]
                                                           |
                                                           v
                                              [Leave Request Store]
                                              [Leave Balance Store]
                                                           |
[Employee History UI] <---------- read status/comment -----+
```

Prefer one approve use-case service invoked by the API; keep UI thin and domain rules server-side.

## Components and responsibilities

| Component | Responsibility |
|-----------|----------------|
| `src/web/manager-dashboard` | Render pending leave list; show Approve per pending item (AC-01); open/dismiss optional-comment dialog (AC-02, AC-10); show success confirmation (AC-08); remove approved item from local pending list after success (AC-06). |
| `src/web/employee-history` | Display leave history including Approved status and manager comment when present (AC-07). |
| `src/web/shared/ui` | Shared dialog, toast/banner confirmation, and list presentation primitives used by dashboard/history. |
| `src/api/leave-approval` | HTTP (or equivalent) handler for approve command: auth context, request id, optional comment; map domain results to success/error responses. |
| `src/api/leave-queries` | Read APIs for manager pending list and employee history (status + comment fields). |
| `src/domain/leave-approval` | Approve use case: assert Pending; set Approved; attach optional comment; compute/apply balance deduction for leave type/duration; enforce single-transition (AC-03–AC-05, AC-09). |
| `src/domain/leave-balance` | Balance lookup and decrement for employee + leave type; surface insufficient-balance outcome if product rules require blocking `(open question)`. |
| `src/data/leave-request-store` | Persist leave requests (status, leave type, duration, employee id, manager comment). |
| `src/data/leave-balance-store` | Persist per-employee per-leave-type balances. |
| `src/data/unit-of-work` | Transactional boundary so status change, comment save, and balance deduct commit or roll back together. |

## Data flow

1. Manager opens dashboard → query pending requests for acting manager → UI renders Approve per item.
2. Manager clicks Approve → UI opens comment dialog (comment optional; dismiss cancels with no writes).
3. Manager submits dialog → UI calls approve API with request id + optional comment.
4. API authenticates manager → domain loads request → rejects if not Pending (no balance change).
5. Domain sets status to Approved, stores comment (or null/empty as “no comment”), deducts balance for request leave type/duration inside one transaction.
6. On success → API returns confirmation → UI shows success message and drops the item from the pending list.
7. Employee opens history → query returns Approved status and manager comment for that request.

## Integration points

| Integration | Direction | Notes |
|-------------|-----------|-------|
| Auth / session context | Inbound | Identifies acting manager; authorize approve only for managers with access to the request `(assumed existing pattern)`. |
| Manager pending-list query | Read | Source of dashboard rows; post-approve list must exclude Approved. |
| Leave request persistence | Read/Write | Status Pending→Approved; optional manager comment field. |
| Leave balance persistence | Read/Write | Decrement on successful approval; guard against double apply. |
| Employee history query | Read | Exposes status + manager comment to the employee. |
| Notifications / email | Out of scope | Not required by story; do not add unless later requirements change. |

No secrets or credentials belong in this artifact or in committed story code; configure via environment outside the repo as needed.

## NFR considerations

| Area | Approach (high level) |
|------|------------------------|
| Security | Authorize approve to manager-capable users; bind action to request id under that manager’s scope; treat comment as untrusted text (store safely; encode on render to reduce XSS risk). |
| Reliability | Single transactional approve; reject non-Pending transitions without side effects; UI disable/debounce Approve while in flight to reduce double-submit. |
| Performance | Approve is a single-request write path; pending/history reads stay list/query scoped—no bulk workflows. |
| Observability | Log approve outcomes (request id, actor id, success/failure reason) without comment PII beyond what ops already allow; surface distinct client errors for not-found, not-pending, unauthorized, and balance rule failures. |

## Trade-offs

| Choice | Benefit | Cost / alternative |
|--------|---------|-------------------|
| Server-side transactional approve use case | Meets AC-03–AC-05 and AC-09 safely; one place for rules | Slightly more backend structure than UI-only status flip |
| Optional comment as nullable/empty field on request | Matches story; simple persistence | No separate comment entity or audit trail beyond the request record |
| Separate dashboard vs history UI modules | Clear AC mapping; independent evolution | Small duplication of request display fields—mitigate via shared read model/DTO |
| Deduction in same transaction as status change | Prevents approved-without-deduction and double deduction | Requires a unit-of-work/data layer; more than fire-and-forget updates |
| Defer reject/bulk/notifications | Keeps scope to stated ACs | Managers cannot deny leave in this slice; may need a follow-up story |

**Open questions carried forward for design** (from requirements): insufficient balance behavior; comment max length; direct-manager-only vs any dashboard manager; success UX form (toast vs banner); leave unit calculation source; whether an approve API already exists to extend vs greenfield in this workspace.
