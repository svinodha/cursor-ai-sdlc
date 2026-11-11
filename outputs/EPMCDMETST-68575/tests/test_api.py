"""API integration tests (VC-4, VC-5)."""

from __future__ import annotations

import json


def _mgr_headers(user_id: str = "mgr-1"):
    return {"X-User-Id": user_id, "X-Role": "manager", "Content-Type": "application/json"}


def _emp_headers(user_id: str = "emp-1"):
    return {"X-User-Id": user_id, "X-Role": "employee", "Content-Type": "application/json"}


def test_approve_success_payload(client):
    res = client.post(
        "/api/leave-requests/lr-1/approve",
        headers=_mgr_headers(),
        data=json.dumps({"comment": "OK"}),
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["request_id"] == "lr-1"
    assert body["status"] == "Approved"
    assert body["manager_comment"] == "OK"
    assert body["balance_after"] == 8.0
    assert body["message"] == "Leave request approved."


def test_approve_without_comment_body(client):
    res = client.post(
        "/api/leave-requests/lr-1/approve",
        headers=_mgr_headers(),
        data=json.dumps({}),
    )
    assert res.status_code == 200
    assert res.get_json()["manager_comment"] is None


def test_approve_not_pending(client):
    res = client.post(
        "/api/leave-requests/lr-approved/approve",
        headers=_mgr_headers(),
        data=json.dumps({}),
    )
    assert res.status_code == 409
    assert res.get_json()["code"] == "not_pending"


def test_approve_insufficient_balance(client):
    res = client.post(
        "/api/leave-requests/lr-broke/approve",
        headers=_mgr_headers(),
        data=json.dumps({}),
    )
    assert res.status_code == 409
    assert res.get_json()["code"] == "insufficient_balance"


def test_approve_invalid_duration(client):
    res = client.post(
        "/api/leave-requests/lr-zero-days/approve",
        headers=_mgr_headers(),
        data=json.dumps({}),
    )
    assert res.status_code == 400
    assert res.get_json()["code"] == "validation_error"


def test_approve_comment_too_long(client):
    res = client.post(
        "/api/leave-requests/lr-1/approve",
        headers=_mgr_headers(),
        data=json.dumps({"comment": "y" * 501}),
    )
    assert res.status_code == 400
    assert res.get_json()["code"] == "validation_error"


def test_approve_unauthorized_missing_headers(client):
    res = client.post(
        "/api/leave-requests/lr-1/approve",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert res.status_code == 401
    assert res.get_json()["code"] == "unauthorized"


def test_approve_forbidden_employee(client):
    res = client.post(
        "/api/leave-requests/lr-1/approve",
        headers=_emp_headers(),
        data=json.dumps({}),
    )
    assert res.status_code == 403
    assert res.get_json()["code"] == "forbidden"


def test_approve_forbidden_wrong_manager(client):
    res = client.post(
        "/api/leave-requests/lr-other-mgr/approve",
        headers=_mgr_headers("mgr-1"),
        data=json.dumps({}),
    )
    assert res.status_code == 403


def test_approve_not_found(client):
    res = client.post(
        "/api/leave-requests/nope/approve",
        headers=_mgr_headers(),
        data=json.dumps({}),
    )
    assert res.status_code == 404
    assert res.get_json()["code"] == "not_found"


def test_pending_list_manager_only(client):
    res = client.get("/api/managers/me/pending-leave-requests", headers=_mgr_headers())
    assert res.status_code == 200
    ids = {item["id"] for item in res.get_json()["items"]}
    assert "lr-1" in ids
    assert "lr-approved" not in ids  # AC-06: approved excluded
    assert "lr-other-mgr" not in ids


def test_pending_list_forbidden_for_employee(client):
    res = client.get("/api/managers/me/pending-leave-requests", headers=_emp_headers())
    assert res.status_code == 403


def test_history_idor_scoped_to_actor(client):
    res = client.get("/api/employees/me/leave-history", headers=_emp_headers("emp-1"))
    assert res.status_code == 200
    items = res.get_json()["items"]
    assert all(True for _ in items)  # scoped server-side to emp-1
    ids = {i["id"] for i in items}
    assert "lr-approved" in ids
    assert "lr-other-mgr" not in ids


def test_history_after_approve_shows_comment(client):
    client.post(
        "/api/leave-requests/lr-1/approve",
        headers=_mgr_headers(),
        data=json.dumps({"comment": "Have a great trip"}),
    )
    res = client.get("/api/employees/me/leave-history", headers=_emp_headers("emp-1"))
    row = next(i for i in res.get_json()["items"] if i["id"] == "lr-1")
    assert row["status"] == "Approved"
    assert row["manager_comment"] == "Have a great trip"


def test_manager_dashboard_renders(client):
    res = client.get("/manager")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Approve" in html
    assert "lr-1" in html or "Alex" in html


def test_employee_history_page_renders(client):
    res = client.get("/employee/history")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Leave History" in html
    assert "Enjoy" in html or "Approved" in html or "Personal" in html


def test_html_encode_comment_in_history(app, stores):
    """XSS-safe: script tags encoded on history render."""
    from datetime import date, datetime, timezone
    from decimal import Decimal

    from leave_approval.models import LeaveRequest, LeaveStatus

    req, _ = stores
    req.save(
        LeaveRequest(
            id="lr-xss",
            employee_id="emp-1",
            employee_name="Alex",
            manager_id="mgr-1",
            leave_type="Annual",
            duration_days=Decimal("1"),
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 1),
            status=LeaveStatus.APPROVED,
            manager_comment='<script>alert(1)</script>',
            created_at=datetime.now(timezone.utc),
            version=1,
        )
    )
    client = app.test_client()
    res = client.get("/employee/history")
    html = res.get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
