"""Tests for certo.check.shell module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.check import check_spec
from certo.check.core import CheckContext
from certo.check.shell import ShellCheck, ShellRunner
from certo.spec import Claim


def test_shell_check_passes() -> None:
    """Test shell check that passes."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-echo"
text = "Echo works"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "echo hello world"
matches = ["hello", "world"]
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].claim_id == "c-echo"
        assert results[0].passed
        assert results[0].kind == "shell"


def test_shell_check_exit_code_fail() -> None:
    """Test shell check fails on wrong exit code."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-fail"
text = "This should fail"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "exit 1"
exit_code = 0
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].claim_id == "c-fail"
        assert not results[0].passed
        assert "exit code" in results[0].message.lower()


def test_shell_check_expected_exit_code() -> None:
    """Test shell check with expected non-zero exit code."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-exit1"
text = "Should exit 1"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "exit 1"
exit_code = 1
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].claim_id == "c-exit1"
        assert results[0].passed


def test_shell_check_matches_fail() -> None:
    """Test shell check fails when pattern not found."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-match"
text = "Pattern matching"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "echo hello"
matches = ["goodbye"]
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].claim_id == "c-match"
        assert not results[0].passed
        assert "pattern not found" in results[0].message.lower()


def test_shell_check_not_matches_fail() -> None:
    """Test shell check fails when forbidden pattern found."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-not-match"
text = "No error messages"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "echo ERROR something went wrong"
not_matches = ["ERROR"]
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].claim_id == "c-not-match"
        assert not results[0].passed
        assert "forbidden pattern found" in results[0].message.lower()


def test_shell_check_regex_matches() -> None:
    """Test shell check with regex patterns."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text(r"""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-regex"
text = "Regex matching"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "echo version 1.2.3"
matches = ["version \\d+\\.\\d+\\.\\d+"]
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].claim_id == "c-regex"
        assert results[0].passed


def test_shell_check_no_cmd() -> None:
    """Test shell check fails with no command."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-no-cmd"
text = "No command"
status = "confirmed"

[[claims.checks]]
kind = "shell"
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].claim_id == "c-no-cmd"
        assert not results[0].passed
        assert "no command" in results[0].message.lower()


def test_shell_check_timeout() -> None:
    """Test shell check with timeout."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-timeout"
text = "Should timeout"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "sleep 10"
timeout = 1
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].claim_id == "c-timeout"
        assert not results[0].passed
        assert "timed out" in results[0].message.lower()


def test_shell_check_cwd() -> None:
    """Test shell check runs in project root."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-cwd"
text = "Runs in project root"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "test -d .certo"
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].claim_id == "c-cwd"
        assert results[0].passed


def test_shell_check_not_matches_fails() -> None:
    """Test shell check fails when not_matches pattern is found."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = ShellCheck(cmd="echo 'ERROR: something bad'", not_matches=["ERROR"])

        result = ShellRunner().run(ctx, claim, check)
        assert not result.passed
        assert "forbidden" in result.message.lower()


def test_shell_check_command_exception() -> None:
    """Test shell check handles unexpected exceptions."""
    from unittest.mock import patch

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = ShellCheck(cmd="echo hello")

        with patch("subprocess.run", side_effect=OSError("mock error")):
            result = ShellRunner().run(ctx, claim, check)

        assert not result.passed
        assert "failed" in result.message.lower()


def test_shell_check_not_matches_passes_when_no_match() -> None:
    """Test shell check passes when not_matches pattern is not found."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = ShellCheck(cmd="echo 'all good'", not_matches=["ERROR", "FAIL"])

        result = ShellRunner().run(ctx, claim, check)
        assert result.passed
