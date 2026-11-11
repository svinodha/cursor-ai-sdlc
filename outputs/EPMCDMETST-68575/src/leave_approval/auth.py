"""Acting user context and demo-only header parsing.

IMPORTANT: X-User-Id / X-Role header trust is DEMO-ONLY and must NOT be used
as a production authentication mechanism. Production must replace this with
real session/auth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, Optional

from leave_approval.errors import Unauthorized

Role = Literal["manager", "employee"]


@dataclass(frozen=True)
class ActingUser:
    user_id: str
    role: Role


def parse_demo_headers(headers: Mapping[str, str]) -> ActingUser:
    """Parse demo identity from request headers.

    Demo-only: any client can spoof these headers. Not production-safe.
    """
    # Case-insensitive header lookup
    normalized = {str(k).lower(): str(v) for k, v in headers.items()}
    user_id = (normalized.get("x-user-id") or "").strip()
    role_raw = (normalized.get("x-role") or "").strip().lower()

    if not user_id:
        raise Unauthorized("Missing X-User-Id header (demo auth).")
    if role_raw not in ("manager", "employee"):
        raise Unauthorized("Missing or invalid X-Role header (demo auth).")

    return ActingUser(user_id=user_id, role=role_raw)  # type: ignore[arg-type]


def require_manager(actor: Optional[ActingUser]) -> ActingUser:
    if actor is None:
        raise Unauthorized("Not authenticated.")
    if actor.role != "manager":
        from leave_approval.errors import Forbidden

        raise Forbidden("Only managers may perform this action.")
    return actor
