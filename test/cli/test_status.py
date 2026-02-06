"""Tests for certo.cli.status module - non-example tests."""

from __future__ import annotations

from certo.cli.status import _get_item_type


def test_get_item_type() -> None:
    """Test _get_item_type function."""
    assert _get_item_type("c-abc1234") == "claim"
    assert _get_item_type("c-xyz") == "claim"
    assert _get_item_type("i-abc1234") == "issue"
    assert _get_item_type("i-xyz") == "issue"
    assert _get_item_type("k-abc1234") == "check"
    assert _get_item_type("k-xyz") == "check"
    assert _get_item_type("d1") is None
    assert _get_item_type("unknown") is None
