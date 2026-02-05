"""Tests for certo.cli.kb module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from certo.cli import main

if TYPE_CHECKING:
    from pytest import CaptureFixture


def test_main_kb_no_subcommand(capsys: CaptureFixture[str]) -> None:
    """Test kb command without subcommand shows help."""
    result = main(["kb"])
    assert result == 0
    captured = capsys.readouterr()
    assert "update" in captured.out


def test_main_kb_update_python(
    capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test kb update python command."""
    monkeypatch.setattr("certo.kb.update.update_python", lambda verbose: True)

    result = main(["kb", "update", "python"])
    assert result == 0
    captured = capsys.readouterr()
    assert "python" in captured.out.lower()


def test_main_kb_update_all(
    capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test kb update command (all sources)."""
    monkeypatch.setattr("certo.kb.update.update_all", lambda verbose: 1)

    result = main(["kb", "update"])
    assert result == 0
    captured = capsys.readouterr()
    assert "1" in captured.out


def test_main_kb_update_failure(
    capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test kb update python command failure."""
    monkeypatch.setattr("certo.kb.update.update_python", lambda verbose: False)

    result = main(["kb", "update", "python"])
    assert result == 1
    captured = capsys.readouterr()
    assert "failed" in captured.err.lower()
