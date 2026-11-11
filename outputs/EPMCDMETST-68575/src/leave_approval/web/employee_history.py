"""Employee leave history page (AC-07) — distinct seeded employee actor."""

from __future__ import annotations

from flask import Blueprint, current_app, render_template, request

from leave_approval.auth import ActingUser
from leave_approval.errors import DomainError
from leave_approval.services.queries import LeaveQueryService
from leave_approval.web.shared_ui import format_comment_cell, status_badge

employee_bp = Blueprint("employee_history", __name__)

# Distinct employee for history demo (not the manager)
DEFAULT_EMPLOYEE_ID = "emp-1"


@employee_bp.get("/employee/history")
def employee_history():
    user_id = (
        request.args.get("as")
        or request.headers.get("X-User-Id")
        or DEFAULT_EMPLOYEE_ID
    )
    actor = ActingUser(user_id=user_id, role="employee")
    queries: LeaveQueryService = current_app.config["QUERY_SERVICE"]
    try:
        rows = queries.leave_history_for_employee(actor)
    except DomainError:
        rows = []
    return render_template(
        "employee_history.html",
        rows=rows,
        actor_id=actor.user_id,
        status_badge=status_badge,
        format_comment=format_comment_cell,
    )
