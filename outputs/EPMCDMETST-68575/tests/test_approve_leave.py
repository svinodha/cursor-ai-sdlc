"""Domain unit tests for ApproveLeaveRequest (VC-1, VC-2, VC-3)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

import pytest

from leave_approval.auth import ActingUser
from leave_approval.errors import (
    Forbidden,
    InsufficientBalance,
    NotFound,
    NotPending,
    ValidationError,
)
from leave_approval.models import LeaveStatus
from leave_approval.services.approve_leave import COMMENT_MAX_LENGTH, normalize_comment


def test_approve_with_comment(approve_service, stores, manager):
    req, bal = stores
    result = approve_service.execute(manager, "lr-1", comment="  Looks good  ")
    assert result.status == LeaveStatus.APPROVED
    assert result.manager_comment == "Looks good"
    assert result.balance_after == Decimal("8.0")
    assert result.message == "Leave request approved."

    saved = req.get("lr-1")
    assert saved is not None
    assert saved.status == LeaveStatus.APPROVED
    assert saved.manager_comment == "Looks good"
    assert saved.approved_by == "mgr-1"
    assert bal.get("emp-1", "Annual").days_remaining == Decimal("8.0")


def test_approve_without_comment(approve_service, stores, manager):
    req, bal = stores
    result = approve_service.execute(manager, "lr-1", comment="   ")
    assert result.status == LeaveStatus.APPROVED
    assert result.manager_comment is None
    assert req.get("lr-1").manager_comment is None
    assert bal.get("emp-1", "Annual").days_remaining == Decimal("8.0")


def test_approve_omitted_comment(approve_service, manager):
    result = approve_service.execute(manager, "lr-1", comment=None)
    assert result.manager_comment is None


def test_not_pending_no_balance_change(approve_service, stores, manager):
    _, bal = stores
    before = bal.get("emp-1", "Annual").days_remaining
    with pytest.raises(NotPending):
        approve_service.execute(manager, "lr-approved", comment="x")
    assert bal.get("emp-1", "Annual").days_remaining == before


def test_insufficient_balance_blocks(approve_service, stores, manager):
    req, bal = stores
    with pytest.raises(InsufficientBalance):
        approve_service.execute(manager, "lr-broke", comment=None)
    assert req.get("lr-broke").status == LeaveStatus.PENDING
    assert bal.get("emp-broke", "Annual").days_remaining == Decimal("1.0")


def test_invalid_duration_rejected(approve_service, stores, manager):
    req, bal = stores
    before = bal.get("emp-1", "Annual").days_remaining
    with pytest.raises(ValidationError):
        approve_service.execute(manager, "lr-zero-days")
    assert req.get("lr-zero-days").status == LeaveStatus.PENDING
    assert bal.get("emp-1", "Annual").days_remaining == before


def test_forbidden_non_manager(approve_service, employee):
    with pytest.raises(Forbidden):
        approve_service.execute(employee, "lr-1")


def test_forbidden_wrong_manager(approve_service, manager):
    with pytest.raises(Forbidden):
        approve_service.execute(manager, "lr-other-mgr")


def test_not_found(approve_service, manager):
    with pytest.raises(NotFound):
        approve_service.execute(manager, "missing")


def test_comment_too_long():
    with pytest.raises(ValidationError):
        normalize_comment("x" * (COMMENT_MAX_LENGTH + 1))


def test_concurrent_double_submit_single_deduction(approve_service, stores, manager):
    """VC-3: one success, second not_pending, balance deducted once."""
    req, bal = stores
    before = bal.get("emp-1", "Annual").days_remaining
    results = []
    errors = []

    def attempt():
        try:
            return ("ok", approve_service.execute(manager, "lr-1", comment="race"))
        except NotPending as exc:
            return ("not_pending", exc)
        except Exception as exc:  # pragma: no cover
            return ("other", exc)

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(attempt) for _ in range(8)]
        for fut in as_completed(futures):
            kind, payload = fut.result()
            if kind == "ok":
                results.append(payload)
            else:
                errors.append((kind, payload))

    assert len(results) == 1
    assert all(k == "not_pending" for k, _ in errors)
    assert req.get("lr-1").status == LeaveStatus.APPROVED
    assert bal.get("emp-1", "Annual").days_remaining == before - Decimal("2.0")


def test_sequential_double_submit(approve_service, stores, manager):
    _, bal = stores
    approve_service.execute(manager, "lr-1")
    after_first = bal.get("emp-1", "Annual").days_remaining
    with pytest.raises(NotPending):
        approve_service.execute(manager, "lr-1")
    assert bal.get("emp-1", "Annual").days_remaining == after_first
