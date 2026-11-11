"""Flask app factory + seed fixtures for the leave-approval demo.

Demo auth via X-User-Id / X-Role is NOT production-safe. Replace with real
session/auth before any production use.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from flask import Flask, redirect

from leave_approval.api.routes import register_api
from leave_approval.models import LeaveBalance, LeaveRequest, LeaveStatus
from leave_approval.services.approve_leave import ApproveLeaveRequest
from leave_approval.services.queries import LeaveQueryService
from leave_approval.stores import InMemoryLeaveBalanceStore, InMemoryLeaveRequestStore
from leave_approval.unit_of_work import UnitOfWork, new_unit_of_work
from leave_approval.web.employee_history import employee_bp
from leave_approval.web.manager_dashboard import manager_bp

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PACKAGE_DIR / "web" / "templates"
STATIC_DIR = PACKAGE_DIR / "web" / "static"

# Seeded demo actors
MANAGER_ID = "mgr-1"
EMPLOYEE_ID = "emp-1"
EMPLOYEE_2_ID = "emp-2"


def seed_demo_data(
    request_store: InMemoryLeaveRequestStore,
    balance_store: InMemoryLeaveBalanceStore,
) -> None:
    """Seed pending requests, balances, manager + distinct employee."""
    now = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    requests = [
        LeaveRequest(
            id="lr-1001",
            employee_id=EMPLOYEE_ID,
            employee_name="Alex Employee",
            manager_id=MANAGER_ID,
            leave_type="Annual",
            duration_days=Decimal("2.0"),
            start_date=date(2026, 4, 6),
            end_date=date(2026, 4, 7),
            status=LeaveStatus.PENDING,
            created_at=now,
            version=0,
        ),
        LeaveRequest(
            id="lr-1002",
            employee_id=EMPLOYEE_2_ID,
            employee_name="Blake Teammate",
            manager_id=MANAGER_ID,
            leave_type="Sick",
            duration_days=Decimal("1.0"),
            start_date=date(2026, 3, 20),
            end_date=date(2026, 3, 20),
            status=LeaveStatus.PENDING,
            created_at=now,
            version=0,
        ),
        LeaveRequest(
            id="lr-1003",
            employee_id=EMPLOYEE_ID,
            employee_name="Alex Employee",
            manager_id=MANAGER_ID,
            leave_type="Annual",
            duration_days=Decimal("3.0"),
            start_date=date(2026, 5, 11),
            end_date=date(2026, 5, 13),
            status=LeaveStatus.PENDING,
            created_at=now,
            version=0,
        ),
        # Already approved — for history demo / AC-09
        LeaveRequest(
            id="lr-0900",
            employee_id=EMPLOYEE_ID,
            employee_name="Alex Employee",
            manager_id=MANAGER_ID,
            leave_type="Personal",
            duration_days=Decimal("1.0"),
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 10),
            status=LeaveStatus.APPROVED,
            manager_comment="Enjoy your day off.",
            created_at=now,
            approved_at=now,
            approved_by=MANAGER_ID,
            version=1,
        ),
        # Non-pending cancelled — AC-09
        LeaveRequest(
            id="lr-0800",
            employee_id=EMPLOYEE_ID,
            employee_name="Alex Employee",
            manager_id=MANAGER_ID,
            leave_type="Annual",
            duration_days=Decimal("1.0"),
            start_date=date(2026, 1, 15),
            end_date=date(2026, 1, 15),
            status=LeaveStatus.CANCELLED,
            created_at=now,
            version=1,
        ),
    ]
    balances = [
        LeaveBalance(EMPLOYEE_ID, "Annual", Decimal("10.0")),
        LeaveBalance(EMPLOYEE_ID, "Sick", Decimal("5.0")),
        LeaveBalance(EMPLOYEE_ID, "Personal", Decimal("2.0")),
        LeaveBalance(EMPLOYEE_2_ID, "Sick", Decimal("3.0")),
        LeaveBalance(EMPLOYEE_2_ID, "Annual", Decimal("8.0")),
        # Insufficient-balance scenario seed (0 remaining for Personal)
        LeaveBalance(EMPLOYEE_2_ID, "Personal", Decimal("0")),
    ]
    request_store.seed(requests)
    balance_store.seed(balances)


def create_app(
    *,
    seed: bool = True,
    request_store: InMemoryLeaveRequestStore | None = None,
    balance_store: InMemoryLeaveBalanceStore | None = None,
) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(TEMPLATE_DIR),
        static_folder=str(STATIC_DIR),
        static_url_path="/static",
    )

    request_store = request_store or InMemoryLeaveRequestStore()
    balance_store = balance_store or InMemoryLeaveBalanceStore()
    if seed:
        seed_demo_data(request_store, balance_store)

    def uow_factory() -> UnitOfWork:
        return new_unit_of_work(request_store, balance_store)

    approve_service = ApproveLeaveRequest(uow_factory=uow_factory)
    query_service = LeaveQueryService(request_store)

    app.config["REQUEST_STORE"] = request_store
    app.config["BALANCE_STORE"] = balance_store
    app.config["APPROVE_SERVICE"] = approve_service
    app.config["QUERY_SERVICE"] = query_service

    register_api(app)
    app.register_blueprint(manager_bp)
    app.register_blueprint(employee_bp)

    @app.get("/")
    def index():
        return redirect("/manager")

    return app


def main() -> None:
    app = create_app()
    # Local demo server only
    app.run(host="127.0.0.1", port=5055, debug=True)


if __name__ == "__main__":
    main()
