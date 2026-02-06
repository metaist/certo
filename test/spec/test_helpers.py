"""Tests for spec helper functions."""

from __future__ import annotations

from datetime import datetime, timezone

from certo.spec import format_datetime, generate_id, now_utc


def test_generate_id() -> None:
    """Test ID generation."""
    id1 = generate_id("c", "Test claim one")
    id2 = generate_id("c", "Test claim two")
    id3 = generate_id("c", "Test claim one")  # Same text as id1
    assert id1.startswith("c-")
    assert id2.startswith("c-")
    assert len(id1) == 9  # c- + 7 hex chars
    # Different text = different ID
    assert id1 != id2
    # Same text = same ID (content-addressable)
    assert id1 == id3


def test_now_utc() -> None:
    """Test now_utc returns UTC datetime."""
    dt = now_utc()
    assert dt.tzinfo is not None
    offset = dt.tzinfo.utcoffset(dt)
    assert offset is not None
    assert offset.total_seconds() == 0


def test_format_datetime() -> None:
    """Test datetime formatting."""
    dt = datetime(2026, 2, 5, 12, 30, 45, tzinfo=timezone.utc)
    assert format_datetime(dt) == "2026-02-05T12:30:45Z"
    assert format_datetime(None) == ""
