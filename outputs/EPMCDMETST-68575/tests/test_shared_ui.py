"""Shared UI helper tests."""

from leave_approval.web.shared_ui import format_comment_cell, html_encode, status_badge


def test_html_encode_escapes():
    assert "&lt;b&gt;" in html_encode("<b>")
    assert html_encode(None) == ""


def test_format_comment_empty():
    assert "muted" in format_comment_cell(None)
    assert "muted" in format_comment_cell("")


def test_status_badge():
    assert "Approved" in status_badge("Approved")
    assert "status-approved" in status_badge("Approved")
