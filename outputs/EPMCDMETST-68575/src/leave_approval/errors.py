"""Typed domain errors for leave approval."""

from __future__ import annotations


class DomainError(Exception):
    """Base domain error with a stable machine code."""

    code: str = "domain_error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)
        self.message = message or self.code


class Unauthorized(DomainError):
    code = "unauthorized"


class Forbidden(DomainError):
    code = "forbidden"


class NotFound(DomainError):
    code = "not_found"


class NotPending(DomainError):
    code = "not_pending"


class InsufficientBalance(DomainError):
    code = "insufficient_balance"


class ValidationError(DomainError):
    code = "validation_error"
