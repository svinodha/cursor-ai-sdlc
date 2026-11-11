# Design Review — EPMCDMETST-68575

## Summary

Review of [design.md](./design.md) against [jira-story.md](./jira-story.md), [requirement-analysis.md](./requirement-analysis.md), and [architecture.md](./architecture.md).

The design is AC-complete for the approve path: optional-comment dialog, atomic Pending→Approved + comment + balance deduct, pending-list removal, employee history visibility, success toast, cancel no-op, and safe non-Pending handling. It follows the architecture’s layered, server-side use-case shape and records explicit `(design default)` answers for open product questions. No blockers found; a few majors should be accepted as risk or tightened in the implementation plan before coding.

## Findings

| Severity | Issue | Recommendation |
|----------|-------|----------------|
| major | Product rules still defaulted, not confirmed: insufficient balance **blocks**; comment max **500**; approver scope = `request.manager_id`; deduct `duration_days` only. Story/requirements left these open. | Explicitly **accept** these defaults for the workspace demo in the implementation plan, or get product confirmation before coding balance/scope behavior. Do not silently change them mid-implementation. |
| major | Concurrent double-approve: design relies on UoW + status check and “prefer compare-and-set / reload-inside-transaction,” but the in-memory store has no concrete lock/mutex/version field specified. Race risk for double deduction if two threads interleave. | In implementation plan: require reload-or-CAS **inside** the UoW (e.g. version/`status` check under a store lock) and a test for concurrent/double submit → single deduction + second `not_pending`. |
| major | Demo auth via `X-User-Id` / `X-Role` allows trivial role spoofing if mistaken for a production pattern. | Keep as **demo-only**; document in plan/README that production must replace with real session/auth. Do not treat header trust as sufficient outside this workspace. |
| minor | UI stack left open (“templates or thin JS/HTMX”). Fine for design, but planning needs one choice to avoid thrash. | Pick one approach in the implementation plan (prefer simplest that meets AC-01/02/06/08/10). |
| minor | No validation for `duration_days <= 0` (or missing duration) before deduct. Could approve with a no-op or nonsense deduction. | Reject invalid duration at approve (400/domain error) or assert seed data always has positive duration; cover in tests. |
| minor | Client error UX for `insufficient_balance` / `not_pending` is sketched but not tied to dialog state (keep dialog open vs close + toast). | Specify in plan: on 409/400 keep dialog open (or re-open) with inline/toast error; only close + success toast on 200. |
| minor | Employee history allows “manager viewing self as employee in demo,” which can blur AC-07 demo path. | Seed a distinct employee actor for history demo; keep IDOR rule (history scoped to acting user only). |

No over-engineering relative to architecture: single approve use case, protocol stores, and thin API/UI match the proposed slice. Reject/bulk/notifications correctly stay out of scope.

## Requirement coverage

| ID | Criterion | Design coverage | Notes |
|----|-----------|-----------------|-------|
| AC-01 | Approve control per pending request | Covered | `manager_dashboard` + pending query |
| AC-02 | Optional comment dialog | Covered | Empty/whitespace → `null`; max 500 |
| AC-03 | Pending → Approved | Covered | `ApproveLeaveRequest` + status enum |
| AC-04 | Comment saved when provided | Covered | `manager_comment` on request |
| AC-05 | Balance deducted for leave type | Covered | Decrement by `duration_days` `(design default)` |
| AC-06 | Removed from pending list | Covered | Local row drop + query excludes Approved |
| AC-07 | Employee history status + comment | Covered | History query + `employee_history` UI |
| AC-08 | Manager success confirmation | Covered | Toast “Leave request approved.” |
| AC-09 | Non-Pending fails without double deduct | Covered | 409 `not_pending`; concurrency caveat above |
| AC-10 | Dialog dismiss = no writes | Covered | Cancel/Esc/overlay; no API call |

Architecture alignment: components, transactional approve, auth scope, XSS-safe comment rendering, and out-of-scope notifications match [architecture.md](./architecture.md). Greenfield Python package under `outputs/EPMCDMETST-68575/src/` matches the workspace constraint.

## Residual risks

- **Product default mismatch:** If real policy allows negative balance or different approver scope, demo behavior will diverge until defaults are revised.
- **In-memory concurrency:** Without an explicit lock/CAS in the store/UoW, AC-09 under parallel submits remains a residual reliability risk.
- **Leave units simplification:** Using only `duration_days` (no holidays/hours/proration) may under/over-deduct vs real HR rules — acceptable for this story’s non-goals, but not production-accurate.
- **Comment content:** Length-capped plain text + encode-on-render mitigates XSS; no moderation beyond that.

## Recommendation

**conditional-go**

Proceed to implementation planning. Do not rewrite the design. Before coding, the plan must (1) record acceptance of the listed design defaults (or note product overrides), (2) specify concrete concurrency control for the in-memory approve transaction, and (3) mark demo header auth as non-production. Address minor findings in plan/tests as practical; none block planning.
