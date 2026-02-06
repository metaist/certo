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
    """Test check command with valid spec."""
    with TemporaryDirectory() as tmpdir:
        certo_dir = Path(tmpdir) / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text('[spec]\nname = "test"\nversion = 1\n')

        result = main(["check", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        # Empty spec = no claims = passed: 0
        assert "passed: 0" in captured.out.lower()


def test_main_check_quiet_success(capsys: CaptureFixture[str]) -> None:
    """Test check command with quiet flag on success."""
    with TemporaryDirectory() as tmpdir:
        certo_dir = Path(tmpdir) / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        result = main(["-q", "check", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        # Quiet mode: no output on success
        assert captured.out == ""


def test_main_check_quiet_failure(capsys: CaptureFixture[str]) -> None:
    """Test check command with quiet flag on failure (missing spec)."""
    with TemporaryDirectory() as tmpdir:
        result = main(["-q", "check", "--path", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        # Shows error in stderr
        assert "not found" in captured.err.lower()


def test_main_check_verbose(capsys: CaptureFixture[str]) -> None:
    """Test check command with verbose flag."""
    with TemporaryDirectory() as tmpdir:
        certo_dir = Path(tmpdir) / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text('[spec]\nname = "test"\n')

        result = main(["-v", "check", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Checking spec:" in captured.out


def test_main_check_json_success(capsys: CaptureFixture[str]) -> None:
    """Test check command with JSON output."""
    with TemporaryDirectory() as tmpdir:
        certo_dir = Path(tmpdir) / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text('[spec]\nname = "test"\nversion = 1\n')

        result = main(["--format", "json", "check", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["passed"] == 0  # Empty spec
        assert data["failed"] == 0
        assert len(data["results"]) == 0


def test_main_check_json_failure(capsys: CaptureFixture[str]) -> None:
    """Test check command with JSON output on failure (missing spec)."""
    with TemporaryDirectory() as tmpdir:
        result = main(["--format", "json", "check", "--path", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["failed"] == 1
        assert "error" in data


def test_main_check_missing_spec(capsys: CaptureFixture[str]) -> None:
    """Test check command with missing spec."""
    with TemporaryDirectory() as tmpdir:
        result = main(["check", "--path", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()


def test_main_check_invalid_toml(capsys: CaptureFixture[str]) -> None:
    """Test check command with invalid TOML."""
    with TemporaryDirectory() as tmpdir:
        certo_dir = Path(tmpdir) / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("invalid [[[toml")

        result = main(["check", "--path", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        assert "failed to parse" in captured.err.lower()


def test_main_check_offline_verbose(capsys: CaptureFixture[str]) -> None:
    """Test check --offline with -v shows verbose message."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        result = main(["-v", "check", "--offline", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "offline" in captured.out.lower()
