"""Tests for certo.cli main module."""

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
    capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test exception handling in text mode."""

    def raise_error(*args: object, **kwargs: object) -> None:
        raise RuntimeError("test error")

    monkeypatch.setattr("certo.cli.check.check_spec", raise_error)

    with TemporaryDirectory() as tmpdir:
        result = main(["check", "--path", tmpdir])
        assert result == 2
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()


def test_main_exception_json(
    capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test exception handling in JSON mode."""

    def raise_error(*args: object, **kwargs: object) -> None:
        raise RuntimeError("test error")

    monkeypatch.setattr("certo.cli.check.check_spec", raise_error)

    with TemporaryDirectory() as tmpdir:
        result = main(["--format", "json", "check", "--path", tmpdir])
        assert result == 2
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "error" in data


def test_normalize_argv_global_flags_before() -> None:
    """Test that global flags before subcommand work."""
    from certo.cli import _normalize_argv

    # -q before scan should be moved after
    result = _normalize_argv(["-q", "scan"])
    assert result == ["scan", "-q"]

    # Multiple flags
    result = _normalize_argv(["-q", "-v", "check", "."])
    assert result == ["check", ".", "-q", "-v"]

    # --format with value
    result = _normalize_argv(["--format", "json", "scan"])
    assert result == ["scan", "--format", "json"]

    # --format=value
    result = _normalize_argv(["--format=json", "scan"])
    assert result == ["scan", "--format=json"]

    # Non-global args before subcommand stay in other_args_before
    # --version is NOT in GLOBAL_FLAGS, so it stays before the subcommand
    result = _normalize_argv(["--version", "scan"])
    assert result == ["--version", "scan"]


def test_normalize_argv_no_subcommand() -> None:
    """Test normalize_argv with no subcommand."""
    from certo.cli import _normalize_argv

    result = _normalize_argv(["--version"])
    assert result == ["--version"]

    result = _normalize_argv([])
    assert result == []


def test_normalize_argv_flags_after() -> None:
    """Test that flags after subcommand stay in place."""
    from certo.cli import _normalize_argv

    result = _normalize_argv(["scan", "-q"])
    assert result == ["scan", "-q"]


def test_main_quiet_before_subcommand(capsys: CaptureFixture[str]) -> None:
    """Test -q flag before subcommand."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')

        result = main(["-q", "scan", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out == ""


def test_main_with_none_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() when argv is None (uses sys.argv)."""
    monkeypatch.setattr("sys.argv", ["certo", "--version"])
    result = main(None)
    assert result == 0
