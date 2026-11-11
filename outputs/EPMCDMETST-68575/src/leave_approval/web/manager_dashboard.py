"""Manager Dashboard page: pending list + Approve dialog (AC-01/02/06/08/10)."""

from __future__ import annotations

from flask import Blueprint, current_app, render_template, request

from leave_approval.auth import ActingUser
from leave_approval.errors import DomainError
from leave_approval.services.queries import LeaveQueryService
from leave_approval.web.shared_ui import format_comment_cell, status_badge

manager_bp = Blueprint("manager_dashboard", __name__)

# Demo defaults — clearly non-production identity selectors
DEFAULT_MANAGER_ID = "mgr-1"


@manager_bp.get("/manager")
def manager_dashboard():
    """Render pending leave for the demo manager actor."""
    # Prefer query param override for demo switching; fall back to header / default.
    user_id = (
        request.args.get("as")
        or request.headers.get("X-User-Id")
        or DEFAULT_MANAGER_ID
    )
    actor = ActingUser(user_id=user_id, role="manager")
    queries: LeaveQueryService = current_app.config["QUERY_SERVICE"]
    try:
        rows = queries.list_pending_for_manager(actor)
    except DomainError:
        rows = []
    return render_template(
        "manager_dashboard.html",
        rows=rows,
        actor_id=actor.user_id,
        status_badge=status_badge,
        format_comment=format_comment_cell,
    )
