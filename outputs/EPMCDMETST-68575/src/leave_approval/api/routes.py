"""Flask API routes for leave approval.

Demo auth via X-User-Id / X-Role is NOT production-safe.
"""

from __future__ import annotations

from flask import Blueprint, Flask, current_app, jsonify, request

from leave_approval.api.schemas import (
    approve_result_to_dict,
    error_body,
    history_row_to_dict,
    parse_approve_body,
    pending_row_to_dict,
)
from leave_approval.auth import parse_demo_headers
from leave_approval.errors import (
    DomainError,
    Forbidden,
    InsufficientBalance,
    NotFound,
    NotPending,
    Unauthorized,
    ValidationError,
)
from leave_approval.services.approve_leave import ApproveLeaveRequest
from leave_approval.services.queries import LeaveQueryService

api_bp = Blueprint("leave_api", __name__)

_HTTP_MAP = {
    Unauthorized: 401,
    Forbidden: 403,
    NotFound: 404,
    NotPending: 409,
    InsufficientBalance: 409,
    ValidationError: 400,
}


def _actor():
    return parse_demo_headers(request.headers)


def _error_response(exc: DomainError):
    status = 500
    for cls, code in _HTTP_MAP.items():
        if isinstance(exc, cls):
            status = code
            break
    return jsonify(error_body(exc.code, exc.message)), status


@api_bp.post("/api/leave-requests/<request_id>/approve")
def approve_leave_request(request_id: str):
    try:
        actor = _actor()
        body = request.get_json(silent=True)
        comment = parse_approve_body(body if body is not None else {})
        service: ApproveLeaveRequest = current_app.config["APPROVE_SERVICE"]
        result = service.execute(actor, request_id, comment)
        return jsonify(approve_result_to_dict(result)), 200
    except DomainError as exc:
        return _error_response(exc)


@api_bp.get("/api/managers/me/pending-leave-requests")
def pending_leave_requests():
    try:
        actor = _actor()
        queries: LeaveQueryService = current_app.config["QUERY_SERVICE"]
        rows = queries.list_pending_for_manager(actor)
        return jsonify({"items": [pending_row_to_dict(r) for r in rows]}), 200
    except DomainError as exc:
        return _error_response(exc)


@api_bp.get("/api/employees/me/leave-history")
def leave_history():
    try:
        actor = _actor()
        queries: LeaveQueryService = current_app.config["QUERY_SERVICE"]
        rows = queries.leave_history_for_employee(actor)
        return jsonify({"items": [history_row_to_dict(r) for r in rows]}), 200
    except DomainError as exc:
        return _error_response(exc)


def register_api(app: Flask) -> None:
    app.register_blueprint(api_bp)
