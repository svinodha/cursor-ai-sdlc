"""Request/response validation helpers for leave approval API."""

from __future__ import annotations

from typing import Any, Optional

from leave_approval.errors import ValidationError
from leave_approval.models import ApproveResult, HistoryRow, PendingRow
from leave_approval.services.approve_leave import COMMENT_MAX_LENGTH, normalize_comment


def parse_approve_body(body: Any) -> Optional[str]:
    """Validate approve JSON body; return normalized comment or None."""
    if body is None:
        return None
    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object.")
    if "comment" not in body:
        return None
    comment = body.get("comment")
    if comment is None:
        return None
    if not isinstance(comment, str):
        raise ValidationError("comment must be a string or null.")
    # normalize_comment enforces max length after trim
    return normalize_comment(comment)


def approve_result_to_dict(result: ApproveResult) -> dict[str, Any]:
    return {
        "request_id": result.request_id,
        "status": result.status.value,
        "manager_comment": result.manager_comment,
        "balance_after": float(result.balance_after),
        "message": result.message,
    }


def pending_row_to_dict(row: PendingRow) -> dict[str, Any]:
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "employee_name": row.employee_name,
        "leave_type": row.leave_type,
        "start_date": row.start_date.isoformat(),
        "end_date": row.end_date.isoformat(),
        "duration_days": float(row.duration_days),
        "status": row.status.value,
    }


def history_row_to_dict(row: HistoryRow) -> dict[str, Any]:
    return {
        "id": row.id,
        "leave_type": row.leave_type,
        "start_date": row.start_date.isoformat(),
        "end_date": row.end_date.isoformat(),
        "duration_days": float(row.duration_days),
        "status": row.status.value,
        "manager_comment": row.manager_comment,
    }


def error_body(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


# Re-export for callers that need the constant
__all__ = [
    "COMMENT_MAX_LENGTH",
    "parse_approve_body",
    "approve_result_to_dict",
    "pending_row_to_dict",
    "history_row_to_dict",
    "error_body",
]
