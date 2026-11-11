# Requirement Analysis — EPMCDMETST-68575

## Problem statement

Managers need a way on the Manager Dashboard to approve pending employee leave requests. Today (or as implied by the story), pending requests must be actioned so employees can proceed with planned leave. Approval must support an optional manager comment, update request status, adjust leave balance, refresh the pending list, and give both manager and employee clear confirmation of the outcome.

## Goals

- Allow a manager to approve each pending leave request from the Manager Dashboard.
- Capture an optional comment during approval and persist it with the request.
- Transition the leave request from **Pending** to **Approved**.
- Deduct the employee’s leave balance for the approved leave type.
- Remove the request from the manager’s pending list after successful approval.
- Surface approved status and any manager comment in the employee’s leave history.
- Show a success confirmation message to the manager after approval.

## Non-goals

- Rejecting, cancelling, or editing leave requests (not stated in the story).
- Bulk/multi-select approval of multiple requests in one action (not stated).
- Changing leave policy rules, accrual formulas, or leave-type configuration beyond deducting balance on approval.
- Employee-side request creation or submission flows.
- Notifications/email beyond what may already exist (not specified) — treat as out of scope unless later clarified.
- Role/permission redesign beyond “manager approving subordinate leave” as implied by the dashboard context.

## Scope

### In scope

- Manager Dashboard UI for pending leave requests: visible **Approve** control per pending request.
- Optional-comment dialog opened when Approve is clicked.
- Backend/status update: Pending → Approved.
- Persistence of optional manager comment on the leave request.
- Leave-balance deduction for the approved leave type / duration associated with the request.
- Removal of the approved request from the manager’s pending list.
- Employee leave history visibility of approved status and manager comment.
- Success confirmation message shown to the manager after a successful approval.

### Out of scope

- Reject / deny leave workflow.
- Mandatory comments (comment is explicitly optional).
- Non-manager actors approving leave.
- Changes unrelated to approval (reporting, analytics, calendar sync) unless already part of existing shared infrastructure.
- Automated tests and PR delivery (later pipeline stages).

## Acceptance criteria

| ID | Criterion | Source |
|----|-----------|--------|
| AC-01 | An **Approve** button (or equivalent control) is displayed for each pending leave request on the Manager Dashboard. | Story AC |
| AC-02 | Clicking **Approve** opens a comment dialog where the manager may enter an optional comment (dialog can be submitted with empty comment). | Story AC |
| AC-03 | On successful approval, the leave request status changes from **Pending** to **Approved**. | Story AC |
| AC-04 | If the manager provides a comment, it is saved and associated with that leave request. | Story AC |
| AC-05 | The employee’s leave balance for the approved leave type is deducted according to the request (type/duration as stored on the request). | Story AC |
| AC-06 | After successful approval, the request no longer appears in the manager’s pending list. | Story AC |
| AC-07 | The employee can see the approved status and any manager comment in their leave history. | Story AC |
| AC-08 | After successful approval, the manager sees a success confirmation message. | Story AC |
| AC-09 | Approving a request that is no longer Pending (e.g. already approved/cancelled) fails safely without double-deducting balance `(inferred)`. | Inferred |
| AC-10 | Cancel/dismiss of the comment dialog does not change request status, balance, or pending list `(inferred)`. | Inferred |

## Assumptions

- “Manager Dashboard” already lists pending leave requests for the authenticated manager’s team; this story adds/extends the approve path rather than building the full dashboard from scratch `(inferred)`.
- Leave request records already store leave type, dates/duration, employee identity, and a status field that includes at least Pending and Approved.
- Leave balance exists per employee per leave type and can be decremented atomically with status change `(inferred)`.
- Only managers (or users with manager dashboard access) can invoke approve; authorization follows existing app patterns `(inferred)`.
- Optional comment may be empty/null; empty comment is treated as “no comment” and does not block approval.
- Employee “history” is an existing or planned view that can display status and manager comment fields.

## Dependencies

- Existing Manager Dashboard pending-leave list UI and data source.
- Leave request domain model/API (status, comment, leave type, duration).
- Leave-balance service or persistence used by the product.
- Employee leave history UI/API capable of showing status and manager comment.
- Authentication/authorization context that identifies the acting manager.

## Risks

- Race conditions: two managers (or double-click) approving the same request could double-deduct balance if concurrency is not guarded.
- Incomplete balance rules: partial days, holidays, or overlapping requests may deduct incorrectly if business rules are underspecified.
- Comment length/content limits and sanitization not specified — risk of storage or XSS issues if free text is rendered unsafely.
- Story does not define error UX (network failure, insufficient balance, unauthorized user) — inconsistent handling if left unspecified.
- Scope ambiguity around whether Approve exists only for Pending items or is merely disabled for others.

## Open questions

1. What happens if the employee’s remaining balance is insufficient for the requested leave — block approval, allow negative, or show a specific error?
2. Are there comment max length, required character set, or moderation rules?
3. Should approval be restricted to the employee’s direct manager only, or any manager with dashboard access to that request?
4. Is success confirmation a toast, inline banner, or modal — and does the dialog close automatically on success?
5. Should the employee be notified (in-app/email) when leave is approved, or is history visibility enough?
6. What exact leave units are deducted (full days, half days, hours), and where is that calculation defined today?
7. Is there an existing approve API/endpoint to extend, or is this greenfield within the dashboard feature set?
