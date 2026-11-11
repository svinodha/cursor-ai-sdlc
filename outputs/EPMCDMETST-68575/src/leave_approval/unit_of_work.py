"""Transactional boundary with store-level mutex for approve CAS."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Iterator, Optional, TypeVar

from leave_approval.models import LeaveBalance, LeaveRequest, LeaveStatus
from leave_approval.stores import InMemoryLeaveBalanceStore, InMemoryLeaveRequestStore

T = TypeVar("T")


@dataclass
class _PendingWrites:
    request: Optional[LeaveRequest] = None
    expected_status: Optional[LeaveStatus] = None
    expected_version: Optional[int] = None
    balance: Optional[LeaveBalance] = None


@dataclass
class UnitOfWork:
    """In-memory UoW: holds a mutex, stages writes, commits with status CAS.

    Approve path must reload the request inside the locked transaction and
    commit via compare-and-set so concurrent approves yield one success and
    one not_pending with a single balance deduction.
    """

    request_store: InMemoryLeaveRequestStore
    balance_store: InMemoryLeaveBalanceStore
    _lock: threading.RLock = field(init=False)
    _writes: _PendingWrites = field(default_factory=_PendingWrites)
    _active: bool = False

    def __post_init__(self) -> None:
        # Prefer request store lock as the shared transaction mutex.
        self._lock = self.request_store.lock

    @contextmanager
    def begin(self) -> Iterator["UnitOfWork"]:
        with self._lock:
            self._writes = _PendingWrites()
            self._active = True
            try:
                yield self
                self.commit()
            except Exception:
                self.rollback()
                raise
            finally:
                self._active = False

    def run(self, fn: Callable[["UnitOfWork"], T]) -> T:
        with self.begin() as uow:
            return fn(uow)

    def get_request(self, request_id: str) -> Optional[LeaveRequest]:
        return self.request_store.get(request_id)

    def get_balance(self, employee_id: str, leave_type: str) -> Optional[LeaveBalance]:
        return self.balance_store.get(employee_id, leave_type)

    def stage_approve(
        self,
        request: LeaveRequest,
        expected_status: LeaveStatus,
        expected_version: int,
        balance: LeaveBalance,
    ) -> None:
        if not self._active:
            raise RuntimeError("UnitOfWork is not active")
        self._writes.request = request
        self._writes.expected_status = expected_status
        self._writes.expected_version = expected_version
        self._writes.balance = balance

    def commit(self) -> None:
        writes = self._writes
        if writes.request is None:
            return
        assert writes.expected_status is not None
        assert writes.expected_version is not None
        assert writes.balance is not None

        ok = self.request_store.compare_and_set_status(
            request_id=writes.request.id,
            expected_status=writes.expected_status,
            expected_version=writes.expected_version,
            entity=writes.request,
        )
        if not ok:
            from leave_approval.errors import NotPending

            raise NotPending("Leave request is no longer pending.")
        self.balance_store.save(writes.balance)
        self._writes = _PendingWrites()

    def rollback(self) -> None:
        self._writes = _PendingWrites()


def new_unit_of_work(
    request_store: InMemoryLeaveRequestStore,
    balance_store: InMemoryLeaveBalanceStore,
) -> UnitOfWork:
    return UnitOfWork(request_store=request_store, balance_store=balance_store)
