"""ApproveLeaveRequest use case: Pending→Approved + comment + balance deduct."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable, Optional

from leave_approval.auth import ActingUser
from leave_approval.errors import (
    Forbidden,
    InsufficientBalance,
    NotFound,
    NotPending,
    ValidationError,
)
from leave_approval.models import ApproveResult, LeaveBalance, LeaveStatus
from leave_approval.unit_of_work import UnitOfWork

COMMENT_MAX_LENGTH = 500


def normalize_comment(comment: Optional[str]) -> Optional[str]:
    if comment is None:
        return None
    trimmed = comment.strip()
    if not trimmed:
        return None
    if len(trimmed) > COMMENT_MAX_LENGTH:
        raise ValidationError(
            f"Comment must be at most {COMMENT_MAX_LENGTH} characters."
        )
    return trimmed


class ApproveLeaveRequest:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def execute(
        self,
        actor: ActingUser,
        request_id: str,
        comment: Optional[str] = None,
    ) -> ApproveResult:
        if actor.role != "manager":
            raise Forbidden("Only managers may approve leave requests.")
        if not request_id or not str(request_id).strip():
            raise ValidationError("request_id is required.")

        normalized = normalize_comment(comment)
        uow = self._uow_factory()

        def _approve(tx: UnitOfWork) -> ApproveResult:
            # Reload inside the locked UoW for CAS-safe concurrency.
            request = tx.get_request(request_id)
            if request is None:
                raise NotFound(f"Leave request {request_id} not found.")
            if request.manager_id != actor.user_id:
                raise Forbidden("Request is not in this manager's scope.")
            if request.status != LeaveStatus.PENDING:
                raise NotPending("Leave request is no longer pending.")
            if request.duration_days is None or request.duration_days <= 0:
                raise ValidationError("duration_days must be greater than zero.")

            expected_status = request.status
            expected_version = request.version

            balance = tx.get_balance(request.employee_id, request.leave_type)
            remaining = balance.days_remaining if balance else Decimal("0")
            if remaining < request.duration_days:
                raise InsufficientBalance(
                    "Insufficient leave balance for this request."
                )

            new_remaining = remaining - request.duration_days
            updated_balance = LeaveBalance(
                employee_id=request.employee_id,
                leave_type=request.leave_type,
                days_remaining=new_remaining,
            )

            request.status = LeaveStatus.APPROVED
            request.manager_comment = normalized
            request.approved_at = self._clock()
            request.approved_by = actor.user_id

            tx.stage_approve(
                request=request,
                expected_status=expected_status,
                expected_version=expected_version,
                balance=updated_balance,
            )
            return ApproveResult(
                request_id=request.id,
                status=LeaveStatus.APPROVED,
                manager_comment=normalized,
                balance_after=new_remaining,
                message="Leave request approved.",
            )

        return uow.run(_approve)
