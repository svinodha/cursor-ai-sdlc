"""Read queries for pending leave and employee history (IDOR-safe)."""

from __future__ import annotations

from leave_approval.auth import ActingUser
from leave_approval.errors import Forbidden
from leave_approval.models import HistoryRow, PendingRow
from leave_approval.stores import LeaveRequestStore


class LeaveQueryService:
    def __init__(self, request_store: LeaveRequestStore) -> None:
        self._requests = request_store

    def list_pending_for_manager(self, actor: ActingUser) -> list[PendingRow]:
        if actor.role != "manager":
            raise Forbidden("Only managers may view pending leave requests.")
        rows = self._requests.list_pending_for_manager(actor.user_id)
        return [
            PendingRow(
                id=r.id,
                employee_id=r.employee_id,
                employee_name=r.employee_name or r.employee_id,
                leave_type=r.leave_type,
                start_date=r.start_date,
                end_date=r.end_date,
                duration_days=r.duration_days,
                status=r.status,
            )
            for r in rows
        ]

    def leave_history_for_employee(self, actor: ActingUser) -> list[HistoryRow]:
        """History scoped to the acting user only (IDOR: never take client employee_id)."""
        # Managers may view their own history only when acting as themselves;
        # always scope by actor.user_id — never accept arbitrary employee_id.
        rows = self._requests.list_for_employee(actor.user_id)
        return [
            HistoryRow(
                id=r.id,
                leave_type=r.leave_type,
                start_date=r.start_date,
                end_date=r.end_date,
                duration_days=r.duration_days,
                status=r.status,
                manager_comment=r.manager_comment,
            )
            for r in rows
        ]
