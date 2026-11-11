"""Domain entities, enums, and DTOs for leave approval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class LeaveStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    CANCELLED = "Cancelled"


@dataclass
class LeaveRequest:
    id: str
    employee_id: str
    manager_id: str
    leave_type: str
    duration_days: Decimal
    start_date: date
    end_date: date
    status: LeaveStatus
    manager_comment: Optional[str] = None
    created_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    employee_name: str = ""
    version: int = 0


@dataclass
class LeaveBalance:
    employee_id: str
    leave_type: str
    days_remaining: Decimal


@dataclass(frozen=True)
class PendingRow:
    id: str
    employee_id: str
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    duration_days: Decimal
    status: LeaveStatus


@dataclass(frozen=True)
class HistoryRow:
    id: str
    leave_type: str
    start_date: date
    end_date: date
    duration_days: Decimal
    status: LeaveStatus
    manager_comment: Optional[str]


@dataclass(frozen=True)
class ApproveResult:
    request_id: str
    status: LeaveStatus
    manager_comment: Optional[str]
    balance_after: Decimal
    message: str = "Leave request approved."
