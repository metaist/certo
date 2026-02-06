"""Tests for Issue parsing and serialization."""

from __future__ import annotations

from datetime import datetime, timezone

from certo.spec import Issue


def test_issue_parse_minimal() -> None:
    """Test parsing an issue with minimal fields."""
    data = {"id": "i-abc1234", "text": "Test issue"}
    issue = Issue.parse(data)
    assert issue.id == "i-abc1234"
    assert issue.text == "Test issue"
    assert issue.status == "open"
    assert issue.tags == []
    assert issue.closed_reason == ""


def test_issue_parse_full() -> None:
    """Test parsing an issue with all fields."""
    dt = datetime(2026, 2, 5, 12, 0, 0, tzinfo=timezone.utc)
    data = {
        "id": "i-abc1234",
        "text": "Test issue",
        "status": "closed",
        "tags": ["architecture"],
        "created": dt,
        "updated": dt,
        "closed_reason": "Resolved by c-xxx",
    }
    issue = Issue.parse(data)
    assert issue.id == "i-abc1234"
    assert issue.text == "Test issue"
    assert issue.status == "closed"
    assert issue.tags == ["architecture"]
    assert issue.created == dt
    assert issue.updated == dt
    assert issue.closed_reason == "Resolved by c-xxx"


def test_issue_to_toml() -> None:
    """Test issue TOML serialization."""
    issue = Issue(
        id="i-abc1234",
        text="Test issue",
        status="closed",
        tags=["arch"],
        closed_reason="Done",
    )
    result = issue.to_toml()
    assert "[[issues]]" in result
    assert 'id = "i-abc1234"' in result
    assert 'status = "closed"' in result
    assert 'closed_reason = "Done"' in result


def test_issue_to_toml_with_timestamps() -> None:
    """Test issue TOML serialization with timestamps."""
    dt = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)
    issue = Issue(
        id="i-abc1234",
        text="Test issue",
        status="open",
        created=dt,
        updated=dt,
    )
    result = issue.to_toml()
    assert "created = 2026-02-05T12:00:00Z" in result
    assert "updated = 2026-02-05T12:00:00Z" in result
