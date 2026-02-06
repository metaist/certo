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
        assert "facts" in captured.out.lower()


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


def test_main_scan_verbose(capsys: CaptureFixture[str]) -> None:
    """Test scan command verbose mode."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')

        result = main(["-v", "scan", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "source:" in captured.out


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
        assert "facts" in data
        assert "errors" in data


def test_main_scan_no_facts(capsys: CaptureFixture[str]) -> None:
    """Test scan command with empty directory."""
    with TemporaryDirectory() as tmpdir:
        result = main(["scan", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Facts: 0" in captured.out


def test_main_scan_with_tooling(capsys: CaptureFixture[str]) -> None:
    """Test scan command discovers tooling."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "uv.lock").write_text("")

        result = main(["scan", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "uses.uv" in captured.out


def test_main_scan_with_ci(capsys: CaptureFixture[str]) -> None:
    """Test scan command discovers CI."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yaml").write_text('python-version: ["3.11", "3.12"]')

        result = main(["scan", "--path", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "uses.github-actions" in captured.out
        assert "python.ci-versions" in captured.out
