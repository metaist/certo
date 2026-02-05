"""Tests for certo.cli module."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest

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


def test_main_version_json(capsys: CaptureFixture[str]) -> None:
    """Test --version with JSON output."""
    result = main(["--format", "json", "--version"])
    assert result == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "version" in data


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


def test_output_info(capsys: CaptureFixture[str]) -> None:
    """Test Output.info method."""
    from certo.cli import Output, OutputFormat

    output = Output(quiet=False, verbose=False, fmt=OutputFormat.TEXT)
    output.info("test message")
    captured = capsys.readouterr()
    assert "test message" in captured.out


def test_output_info_quiet(capsys: CaptureFixture[str]) -> None:
    """Test Output.info is suppressed in quiet mode."""
    from certo.cli import Output, OutputFormat

    output = Output(quiet=True, verbose=False, fmt=OutputFormat.TEXT)
    output.info("test message")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_output_error(capsys: CaptureFixture[str]) -> None:
    """Test Output.error method."""
    from certo.cli import Output, OutputFormat

    output = Output(quiet=False, verbose=False, fmt=OutputFormat.TEXT)
    output.error("error message")
    captured = capsys.readouterr()
    assert "error message" in captured.err


def test_output_error_json(capsys: CaptureFixture[str]) -> None:
    """Test Output.error is suppressed in JSON mode."""
    from certo.cli import Output, OutputFormat

    output = Output(quiet=False, verbose=False, fmt=OutputFormat.JSON)
    output.error("error message")
    captured = capsys.readouterr()
    assert captured.err == ""


def test_main_exception_text(
    capsys: CaptureFixture[str], monkeypatch: "pytest.MonkeyPatch"
) -> None:
    """Test exception handling in text mode."""
    import certo.cli

    def raise_error(args: object, output: object) -> int:
        raise RuntimeError("test error")

    monkeypatch.setattr(certo.cli, "cmd_check", raise_error)

    with TemporaryDirectory() as tmpdir:
        result = main(["check", tmpdir])
        assert result == 2
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()


def test_main_exception_json(
    capsys: CaptureFixture[str], monkeypatch: "pytest.MonkeyPatch"
) -> None:
    """Test exception handling in JSON mode."""
    import certo.cli

    def raise_error(args: object, output: object) -> int:
        raise RuntimeError("test error")

    monkeypatch.setattr(certo.cli, "cmd_check", raise_error)

    with TemporaryDirectory() as tmpdir:
        result = main(["--format", "json", "check", tmpdir])
        assert result == 2
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "error" in data
