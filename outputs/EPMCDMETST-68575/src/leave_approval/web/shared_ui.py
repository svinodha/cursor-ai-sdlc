"""Shared UI helpers: HTML encode, dialog/toast markup fragments."""

from __future__ import annotations

import html
from typing import Optional


def html_encode(value: Optional[str]) -> str:
    """Encode untrusted text for safe HTML rendering (XSS mitigation)."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def format_comment_cell(comment: Optional[str]) -> str:
    if not comment:
        return '<span class="muted">—</span>'
    return html_encode(comment)


def status_badge(status: str) -> str:
    safe = html_encode(status)
    css = "status-approved" if status == "Approved" else "status-pending"
    if status == "Cancelled":
        css = "status-cancelled"
    return f'<span class="badge {css}">{safe}</span>'
