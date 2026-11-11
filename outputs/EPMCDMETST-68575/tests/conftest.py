"""Shared fixtures for leave-approval tests."""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

# Ensure story src/ is importable when pytest is run from the story folder
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from leave_approval.app import create_app
from leave_approval.auth import ActingUser
from leave_approval.models import LeaveBalance, LeaveRequest, LeaveStatus
from leave_approval.services.approve_leave import ApproveLeaveRequest
from leave_approval.services.queries import LeaveQueryService
from leave_approval.stores import InMemoryLeaveBalanceStore, InMemoryLeaveRequestStore
from leave_approval.unit_of_work import new_unit_of_work


@pytest.fixture
def stores():
    req = InMemoryLeaveRequestStore()
    bal = InMemoryLeaveBalanceStore()
    now = datetime(2026, 3, 1, tzinfo=timezone.utc)
    req.seed(
        [
            LeaveRequest(
                id="lr-1",
                employee_id="emp-1",
                employee_name="Alex",
                manager_id="mgr-1",
                leave_type="Annual",
                duration_days=Decimal("2.0"),
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 2),
                status=LeaveStatus.PENDING,
                created_at=now,
                version=0,
            ),
            LeaveRequest(
                id="lr-approved",
                employee_id="emp-1",
                employee_name="Alex",
                manager_id="mgr-1",
                leave_type="Annual",
                duration_days=Decimal("1.0"),
                start_date=date(2026, 2, 1),
                end_date=date(2026, 2, 1),
                status=LeaveStatus.APPROVED,
                manager_comment="Prior",
                created_at=now,
                version=1,
            ),
            LeaveRequest(
                id="lr-other-mgr",
                employee_id="emp-9",
                employee_name="Other",
                manager_id="mgr-2",
                leave_type="Annual",
                duration_days=Decimal("1.0"),
                start_date=date(2026, 4, 10),
                end_date=date(2026, 4, 10),
                status=LeaveStatus.PENDING,
                created_at=now,
                version=0,
            ),
            LeaveRequest(
                id="lr-zero-days",
                employee_id="emp-1",
                employee_name="Alex",
                manager_id="mgr-1",
                leave_type="Annual",
                duration_days=Decimal("0"),
                start_date=date(2026, 6, 1),
                end_date=date(2026, 6, 1),
                status=LeaveStatus.PENDING,
                created_at=now,
                version=0,
            ),
            LeaveRequest(
                id="lr-broke",
                employee_id="emp-broke",
                employee_name="Broke",
                manager_id="mgr-1",
                leave_type="Annual",
                duration_days=Decimal("5.0"),
                start_date=date(2026, 7, 1),
                end_date=date(2026, 7, 5),
                status=LeaveStatus.PENDING,
                created_at=now,
                version=0,
            ),
        ]
    )
    bal.seed(
        [
            LeaveBalance("emp-1", "Annual", Decimal("10.0")),
            LeaveBalance("emp-9", "Annual", Decimal("5.0")),
            LeaveBalance("emp-broke", "Annual", Decimal("1.0")),
        ]
    )
    return req, bal


@pytest.fixture
def approve_service(stores):
    req, bal = stores

    def factory():
        return new_unit_of_work(req, bal)

    return ApproveLeaveRequest(uow_factory=factory)


@pytest.fixture
def query_service(stores):
    req, _ = stores
    return LeaveQueryService(req)


@pytest.fixture
def manager():
    return ActingUser(user_id="mgr-1", role="manager")


@pytest.fixture
def employee():
    return ActingUser(user_id="emp-1", role="employee")


@pytest.fixture
def app(stores):
    req, bal = stores
    application = create_app(seed=False, request_store=req, balance_store=bal)
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()
