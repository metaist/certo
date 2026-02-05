"""Tests for certo.cli.check module."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from certo.cli import main

if TYPE_CHECKING:
    from pytest import CaptureFixture


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


def test_main_check_quiet_success(capsys: CaptureFixture[str]) -> None:
    """Test check command with quiet flag on success."""
    with TemporaryDirectory() as tmpdir:
        certo_dir = Path(tmpdir) / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        result = main(["-q", "check", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        # Quiet mode: no output on success
        assert captured.out == ""


def test_main_check_quiet_failure(capsys: CaptureFixture[str]) -> None:
    """Test check command with quiet flag on failure."""
    with TemporaryDirectory() as tmpdir:
        result = main(["-q", "check", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        # Quiet mode still shows failures
        assert "✗" in captured.out


def test_main_check_verbose(capsys: CaptureFixture[str]) -> None:
    """Test check command with verbose flag."""
    with TemporaryDirectory() as tmpdir:
        certo_dir = Path(tmpdir) / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        result = main(["-v", "check", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Strategy:" in captured.out


def test_main_check_json_success(capsys: CaptureFixture[str]) -> None:
    """Test check command with JSON output."""
    with TemporaryDirectory() as tmpdir:
        certo_dir = Path(tmpdir) / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        result = main(["--format", "json", "check", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["passed"] == 1
        assert data["failed"] == 0
        assert len(data["results"]) == 1


def test_main_check_json_failure(capsys: CaptureFixture[str]) -> None:
    """Test check command with JSON output on failure."""
    with TemporaryDirectory() as tmpdir:
        result = main(["--format", "json", "check", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["failed"] == 1


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


def test_main_check_offline_verbose(capsys: CaptureFixture[str]) -> None:
    """Test check --offline with -v shows verbose message."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        result = main(["-v", "check", "--offline", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "offline" in captured.out.lower()
