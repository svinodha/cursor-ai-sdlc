"""Store protocols and thread-safe in-memory implementations with CAS support."""

from __future__ import annotations

import copy
import threading
from decimal import Decimal
from typing import Dict, List, Optional, Protocol, Tuple

from leave_approval.models import LeaveBalance, LeaveRequest, LeaveStatus


class LeaveRequestStore(Protocol):
    def get(self, request_id: str) -> Optional[LeaveRequest]: ...

    def save(self, entity: LeaveRequest) -> None: ...

    def list_pending_for_manager(self, manager_id: str) -> List[LeaveRequest]: ...

    def list_for_employee(self, employee_id: str) -> List[LeaveRequest]: ...

    def compare_and_set_status(
        self,
        request_id: str,
        expected_status: LeaveStatus,
        expected_version: int,
        entity: LeaveRequest,
    ) -> bool: ...


class LeaveBalanceStore(Protocol):
    def get(self, employee_id: str, leave_type: str) -> Optional[LeaveBalance]: ...

    def save(self, balance: LeaveBalance) -> None: ...


class InMemoryLeaveRequestStore:
    """In-memory leave request store. Mutations must go through UnitOfWork lock."""

    def __init__(self) -> None:
        self._items: Dict[str, LeaveRequest] = {}
        self._lock = threading.RLock()

    @property
    def lock(self) -> threading.RLock:
        return self._lock

    def seed(self, requests: List[LeaveRequest]) -> None:
        with self._lock:
            for req in requests:
                self._items[req.id] = copy.deepcopy(req)

    def get(self, request_id: str) -> Optional[LeaveRequest]:
        with self._lock:
            item = self._items.get(request_id)
            return copy.deepcopy(item) if item else None

    def save(self, entity: LeaveRequest) -> None:
        with self._lock:
            self._items[entity.id] = copy.deepcopy(entity)

    def list_pending_for_manager(self, manager_id: str) -> List[LeaveRequest]:
        with self._lock:
            rows = [
                copy.deepcopy(r)
                for r in self._items.values()
                if r.manager_id == manager_id and r.status == LeaveStatus.PENDING
            ]
            rows.sort(key=lambda r: (r.start_date, r.id))
            return rows

    def list_for_employee(self, employee_id: str) -> List[LeaveRequest]:
        with self._lock:
            rows = [
                copy.deepcopy(r)
                for r in self._items.values()
                if r.employee_id == employee_id
            ]
            rows.sort(key=lambda r: (r.start_date, r.id), reverse=True)
            return rows

    def compare_and_set_status(
        self,
        request_id: str,
        expected_status: LeaveStatus,
        expected_version: int,
        entity: LeaveRequest,
    ) -> bool:
        """Atomic status/version check-and-set under the store lock."""
        with self._lock:
            current = self._items.get(request_id)
            if current is None:
                return False
            if current.status != expected_status or current.version != expected_version:
                return False
            updated = copy.deepcopy(entity)
            updated.version = expected_version + 1
            self._items[request_id] = updated
            return True


class InMemoryLeaveBalanceStore:
    def __init__(self) -> None:
        self._items: Dict[Tuple[str, str], LeaveBalance] = {}
        self._lock = threading.RLock()

    @property
    def lock(self) -> threading.RLock:
        return self._lock

    def seed(self, balances: List[LeaveBalance]) -> None:
        with self._lock:
            for bal in balances:
                key = (bal.employee_id, bal.leave_type)
                self._items[key] = copy.deepcopy(bal)

    def get(self, employee_id: str, leave_type: str) -> Optional[LeaveBalance]:
        with self._lock:
            item = self._items.get((employee_id, leave_type))
            return copy.deepcopy(item) if item else None

    def save(self, balance: LeaveBalance) -> None:
        with self._lock:
            self._items[(balance.employee_id, balance.leave_type)] = copy.deepcopy(
                balance
            )

    def get_days(self, employee_id: str, leave_type: str) -> Decimal:
        bal = self.get(employee_id, leave_type)
        return bal.days_remaining if bal else Decimal("0")
