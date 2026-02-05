"""Tests for certo.cli module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from certo.cli import main

if TYPE_CHECKING:
    from pytest import CaptureFixture


def test_main_no_args(capsys: CaptureFixture[str]) -> None:
    """Test main with no arguments shows help."""
    result = main([])
    assert result == 0
    captured = capsys.readouterr()
    assert "certo" in captured.out.lower()


def test_main_version(capsys: CaptureFixture[str]) -> None:
    """Test --version flag."""
    result = main(["--version"])
    assert result == 0
    captured = capsys.readouterr()
    assert "certo" in captured.out.lower()


def test_main_check_success(capsys: CaptureFixture[str]) -> None:
    """Test check command with valid blueprint."""
    with TemporaryDirectory() as tmpdir:
        certo_dir = Path(tmpdir) / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        result = main(["check", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "✓" in captured.out
        assert "passed: 1" in captured.out.lower()


def test_main_check_missing_blueprint(capsys: CaptureFixture[str]) -> None:
    """Test check command with missing blueprint."""
    with TemporaryDirectory() as tmpdir:
        result = main(["check", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        assert "✗" in captured.out
        assert "failed: 1" in captured.out.lower()


def test_main_check_invalid_toml(capsys: CaptureFixture[str]) -> None:
    """Test check command with invalid TOML."""
    with TemporaryDirectory() as tmpdir:
        certo_dir = Path(tmpdir) / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("invalid [[[toml")

        result = main(["check", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        assert "✗" in captured.out
        assert "invalid toml" in captured.out.lower()
