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
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        (certo_dir / "spec.toml").write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "echo hello world"
""")

        output_file = root / "results.json"
        result = main(["check", "--path", tmpdir, "--output", str(output_file)])
        assert result == 0

        # Check output file was created
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["passed"] == 2
        assert data["failed"] == 0
        assert len(data["results"]) == 2

        # Check that output contains command output
        shell_result = [r for r in data["results"] if r["strategy"] == "shell"][0]
        assert "hello world" in shell_result["output"]


def test_check_output_to_stdout(capsys: CaptureFixture[str]) -> None:
    """Test --output - writes to stdout."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        (certo_dir / "spec.toml").write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "echo hello"
""")

        result = main(["check", "--path", tmpdir, "--output", "-"])
        assert result == 0

        captured = capsys.readouterr()
        # Find the JSON block in stdout (it's a multi-line pretty-printed JSON)
        # Look for lines starting with { and ending with }
        lines = captured.out.strip().split("\n")
        json_start = None
        for i, line in enumerate(lines):
            if line.strip() == "{":
                json_start = i
                break
        assert json_start is not None, f"No JSON found in output: {captured.out}"
        json_text = "\n".join(lines[json_start:])
        data = json.loads(json_text)
        assert "passed" in data
        assert "results" in data


def test_check_output_includes_check_id(capsys: CaptureFixture[str]) -> None:
    """Test that output includes check IDs."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        (certo_dir / "spec.toml").write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "shell"
id = "k-custom-id"
cmd = "echo hello"
""")

        output_file = root / "results.json"
        result = main(["check", "--path", tmpdir, "--output", str(output_file)])
        assert result == 0

        data = json.loads(output_file.read_text())
        shell_result = [r for r in data["results"] if r["strategy"] == "shell"][0]
        assert shell_result["check_id"] == "k-custom-id"


def test_check_output_auto_generates_check_id(capsys: CaptureFixture[str]) -> None:
    """Test that check IDs are auto-generated if not provided."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        (certo_dir / "spec.toml").write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "echo hello"
""")

        output_file = root / "results.json"
        result = main(["check", "--path", tmpdir, "--output", str(output_file)])
        assert result == 0

        data = json.loads(output_file.read_text())
        shell_result = [r for r in data["results"] if r["strategy"] == "shell"][0]
        # Should have auto-generated k- prefixed ID
        assert shell_result["check_id"].startswith("k-")
