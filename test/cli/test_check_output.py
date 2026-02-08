"""Tests for certo check --output."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from certo.cli import main

if TYPE_CHECKING:
    from pytest import CaptureFixture


def test_check_output_to_file(capsys: CaptureFixture[str]) -> None:
    """Test --output writes to file."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "certo.toml").write_text("""
[spec]
name = "test"
version = 1

[[probes]]
id = "k-test"
kind = "shell"
cmd = "echo hello world"
""")

        output_file = root / "results.json"
        result = main(["check", "--path", tmpdir, "--output", str(output_file)])
        assert result == 0

        # Check output file was created
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["passed"] == 1
        assert data["failed"] == 0
        assert len(data["results"]) == 1

        # Check that output contains command output
        shell_result = [r for r in data["results"] if r["kind"] == "shell"][0]
        assert "hello world" in shell_result["output"]


def test_check_output_to_stdout(capsys: CaptureFixture[str]) -> None:
    """Test --output - writes to stdout."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "certo.toml").write_text("""
[spec]
name = "test"
version = 1

[[probes]]
id = "k-test"
kind = "shell"
cmd = "echo hello"
""")

        result = main(["check", "--path", tmpdir, "--output", "-"])
        assert result == 0

        captured = capsys.readouterr()
        # stdout should contain JSON
        data = json.loads(captured.out)
        assert data["passed"] == 1


def test_check_output_includes_check_id(capsys: CaptureFixture[str]) -> None:
    """Test --output includes check IDs."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "certo.toml").write_text("""
[spec]
name = "test"
version = 1

[[probes]]
id = "k-custom-id"
kind = "shell"
cmd = "echo test"
""")

        output_file = root / "results.json"
        result = main(["check", "--path", tmpdir, "--output", str(output_file)])
        assert result == 0

        data = json.loads(output_file.read_text())
        shell_result = [r for r in data["results"] if r["kind"] == "shell"][0]
        assert shell_result["probe_id"] == "k-custom-id"


def test_check_output_auto_generates_check_id(capsys: CaptureFixture[str]) -> None:
    """Test --output with auto-generated check ID."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "certo.toml").write_text("""
[spec]
name = "test"
version = 1

[[probes]]
kind = "shell"
cmd = "echo test"
""")

        output_file = root / "results.json"
        result = main(["check", "--path", tmpdir, "--output", str(output_file)])
        assert result == 0

        data = json.loads(output_file.read_text())
        shell_result = [r for r in data["results"] if r["kind"] == "shell"][0]
        # ID should be auto-generated starting with k-
        assert shell_result["probe_id"].startswith("k-")
