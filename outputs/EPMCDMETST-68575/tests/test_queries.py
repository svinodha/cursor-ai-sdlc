"""Query service tests."""

from __future__ import annotations

import pytest

from leave_approval.auth import ActingUser
from leave_approval.errors import Forbidden
from leave_approval.models import LeaveStatus


def test_pending_only_for_manager(query_service, manager):
    rows = query_service.list_pending_for_manager(manager)
    ids = {r.id for r in rows}
    assert "lr-1" in ids
    assert "lr-approved" not in ids
    assert all(r.status == LeaveStatus.PENDING for r in rows)


def test_pending_rejects_employee(query_service, employee):
    with pytest.raises(Forbidden):
        query_service.list_pending_for_manager(employee)


def test_history_scoped_to_actor(query_service, employee):
    rows = query_service.leave_history_for_employee(employee)
    ids = {r.id for r in rows}
    assert "lr-1" in ids
    assert "lr-other-mgr" not in ids


def test_history_does_not_accept_other_employee_id(query_service):
    """IDOR: history always uses actor.user_id, never a client-supplied id."""
    other = ActingUser(user_id="emp-9", role="employee")
    rows = query_service.leave_history_for_employee(other)
    ids = {r.id for r in rows}
    assert ids == {"lr-other-mgr"}
