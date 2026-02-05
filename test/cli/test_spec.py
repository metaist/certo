"""Tests for certo.cli.spec module - non-example tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from certo.cli import main
from certo.cli.spec import _get_item_type

if TYPE_CHECKING:
    from pytest import CaptureFixture


def test_main_spec_no_subcommand(capsys: CaptureFixture[str]) -> None:
    """Test spec command without subcommand shows help."""
    result = main(["spec"])
    assert result == 0
    captured = capsys.readouterr()
    assert "show" in captured.out


def test_get_item_type() -> None:
    """Test _get_item_type function."""
    assert _get_item_type("c-abc1234") == "claim"
    assert _get_item_type("c-xyz") == "claim"
    assert _get_item_type("i-abc1234") == "issue"
    assert _get_item_type("i-xyz") == "issue"
    assert _get_item_type("x-abc1234") == "context"
    assert _get_item_type("x-xyz") == "context"
    assert _get_item_type("d1") is None
    assert _get_item_type("unknown") is None
