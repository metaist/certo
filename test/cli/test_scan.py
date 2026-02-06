"""Tests for certo.cli.scan module."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from certo.cli import main

if TYPE_CHECKING:
    from pytest import CaptureFixture


def test_main_scan_success(capsys: CaptureFixture[str]) -> None:
    """Test scan command with valid project."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')

        result = main(["scan", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "assumptions" in captured.out.lower()


def test_main_scan_quiet_no_issues(capsys: CaptureFixture[str]) -> None:
    """Test scan command quiet mode with no issues."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')

        result = main(["-q", "scan", "--path", tmpdir])
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

        result = main(["-q", "scan", "--path", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        assert "3.10" in captured.out


def test_main_scan_verbose(capsys: CaptureFixture[str]) -> None:
    """Test scan command verbose mode."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')

        result = main(["-v", "scan", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Evidence:" in captured.out


def test_main_scan_json(capsys: CaptureFixture[str]) -> None:
    """Test scan command with JSON output."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')

        result = main(["--format", "json", "scan", "--path", tmpdir])
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

        result = main(["-v", "scan", "--path", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        assert "Sources:" in captured.out


def test_main_scan_no_assumptions(capsys: CaptureFixture[str]) -> None:
    """Test scan command with no pyproject.toml."""
    with TemporaryDirectory() as tmpdir:
        result = main(["scan", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Assumptions: 0" in captured.out


def test_main_scan_warning_issues(capsys: CaptureFixture[str]) -> None:
    """Test scan command with warning-level issues."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text("""
[project]
requires-python = ">=3.11"
classifiers = ["Programming Language :: Python :: 3.9"]
""")

        result = main(["scan", "--path", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        assert "⚠" in captured.out
