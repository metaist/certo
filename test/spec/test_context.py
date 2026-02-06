"""Tests for Context parsing and serialization."""

from __future__ import annotations

from datetime import datetime, timezone

from certo.spec import Context, Modification


def test_context_parse_minimal() -> None:
    """Test parsing a context with minimal fields."""
    data = {"id": "x-abc1234", "name": "Test context"}
    context = Context.parse(data)
    assert context.id == "x-abc1234"
    assert context.name == "Test context"
    assert context.description == ""
    assert context.modifications == []
    assert context.expires is None


def test_context_parse_full() -> None:
    """Test parsing a context with all fields."""
    dt = datetime(2026, 12, 31, tzinfo=timezone.utc)
    data = {
        "id": "x-abc1234",
        "name": "Test context",
        "description": "A test context",
        "created": dt,
        "updated": dt,
        "expires": dt,
        "modifications": [{"action": "relax", "claim": "c-xxx"}],
    }
    context = Context.parse(data)
    assert context.id == "x-abc1234"
    assert context.name == "Test context"
    assert context.description == "A test context"
    assert context.created == dt
    assert context.updated == dt
    assert context.expires == dt
    assert len(context.modifications) == 1
    assert context.modifications[0].action == "relax"


def test_context_to_toml() -> None:
    """Test context TOML serialization."""
    context = Context(
        id="x-abc1234",
        name="release",
        description="For releases",
        modifications=[Modification(action="relax", claim="c-xxx")],
    )
    result = context.to_toml()
    assert "[[contexts]]" in result
    assert 'id = "x-abc1234"' in result
    assert 'name = "release"' in result
    assert "modifications = [" in result


def test_context_to_toml_with_timestamps() -> None:
    """Test context TOML serialization with timestamps."""
    dt = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)
    expires = datetime(2026, 12, 31, tzinfo=timezone.utc)
    context = Context(
        id="x-abc1234",
        name="release",
        created=dt,
        updated=dt,
        expires=expires,
    )
    result = context.to_toml()
    assert "created = 2026-02-05T12:00:00Z" in result
    assert "updated = 2026-02-05T12:00:00Z" in result
    assert "expires = 2026-12-31T00:00:00Z" in result
