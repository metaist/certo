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
    from certo.cli_util import Output, OutputFormat

    output = Output(quiet=False, verbose=False, fmt=OutputFormat.TEXT)
    output.info("test message")
    captured = capsys.readouterr()
    assert "test message" in captured.out


def test_output_info_quiet(capsys: CaptureFixture[str]) -> None:
    """Test Output.info is suppressed in quiet mode."""
    from certo.cli_util import Output, OutputFormat

    output = Output(quiet=True, verbose=False, fmt=OutputFormat.TEXT)
    output.info("test message")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_output_error(capsys: CaptureFixture[str]) -> None:
    """Test Output.error method."""
    from certo.cli_util import Output, OutputFormat

    output = Output(quiet=False, verbose=False, fmt=OutputFormat.TEXT)
    output.error("error message")
    captured = capsys.readouterr()
    assert "error message" in captured.err


def test_output_error_json(capsys: CaptureFixture[str]) -> None:
    """Test Output.error is suppressed in JSON mode."""
    from certo.cli_util import Output, OutputFormat

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


def test_main_scan_success(capsys: CaptureFixture[str]) -> None:
    """Test scan command with valid project."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')

        result = main(["scan", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "assumptions" in captured.out.lower()


def test_main_scan_quiet_no_issues(capsys: CaptureFixture[str]) -> None:
    """Test scan command quiet mode with no issues."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')

        result = main(["-q", "scan", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out == ""


def test_main_scan_quiet_with_issues(capsys: CaptureFixture[str]) -> None:
    """Test scan command quiet mode with issues."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        ci = workflows / "ci.yaml"
        ci.write_text('python-version: ["3.10"]\n')

        result = main(["-q", "scan", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        assert "3.10" in captured.out


def test_main_scan_verbose(capsys: CaptureFixture[str]) -> None:
    """Test scan command verbose mode."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')

        result = main(["-v", "scan", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Evidence:" in captured.out


def test_main_scan_json(capsys: CaptureFixture[str]) -> None:
    """Test scan command with JSON output."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')

        result = main(["--format", "json", "scan", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "assumptions" in data
        assert "issues" in data


def test_main_scan_verbose_with_issues(capsys: CaptureFixture[str]) -> None:
    """Test scan command verbose mode with issues."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        ci = workflows / "ci.yaml"
        ci.write_text('python-version: ["3.10"]\n')

        result = main(["-v", "scan", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        assert "Sources:" in captured.out


def test_main_scan_no_assumptions(capsys: CaptureFixture[str]) -> None:
    """Test scan command with no pyproject.toml."""
    with TemporaryDirectory() as tmpdir:
        result = main(["scan", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Assumptions: 0" in captured.out


def test_main_scan_warning_issues(capsys: CaptureFixture[str]) -> None:
    """Test scan command with warning-level issues."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            """
[project]
requires-python = ">=3.11"
classifiers = ["Programming Language :: Python :: 3.9"]
"""
        )

        result = main(["scan", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        assert "⚠" in captured.out


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

        result = main(["-q", "scan", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out == ""


def test_main_with_none_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() when argv is None (uses sys.argv)."""
    monkeypatch.setattr("sys.argv", ["certo", "--version"])
    result = main(None)
    assert result == 0


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
