"""Tests for certo.check.fact module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.check.core import CheckContext
from certo.check.fact import clear_scan_cache, FactRunner
from certo.spec import Claim
from certo.check import FactCheck


def test_fact_check_has_exists() -> None:
    """Test fact check with 'has' when fact exists."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "uv.lock").write_text("")

        clear_scan_cache()
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Uses uv", status="confirmed")
        check = FactCheck(has="uses.uv")

        result = FactRunner().run(ctx, claim, check)
        assert result.passed
        assert result.passed


def test_fact_check_has_missing() -> None:
    """Test fact check with 'has' when fact is missing."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        clear_scan_cache()
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Uses uv", status="confirmed")
        check = FactCheck(has="uses.uv")

        result = FactRunner().run(ctx, claim, check)
        assert not result.passed
        assert "not found" in result.message


def test_fact_check_equals_match() -> None:
    """Test fact check with 'equals' when values match."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
requires-python = ">=3.11"
""")

        clear_scan_cache()
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Python 3.11+", status="confirmed")
        check = FactCheck(equals="python.min-version", value="3.11")

        result = FactRunner().run(ctx, claim, check)
        assert result.passed
        assert result.passed


def test_fact_check_equals_mismatch() -> None:
    """Test fact check with 'equals' when values don't match."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
requires-python = ">=3.11"
""")

        clear_scan_cache()
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Python 3.12+", status="confirmed")
        check = FactCheck(equals="python.min-version", value="3.12")

        result = FactRunner().run(ctx, claim, check)
        assert not result.passed
        assert "3.11" in result.message  # actual value
        assert "3.12" in result.message  # expected value


def test_fact_check_equals_missing() -> None:
    """Test fact check with 'equals' when fact is missing."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        clear_scan_cache()
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = FactCheck(equals="missing.fact", value="foo")

        result = FactRunner().run(ctx, claim, check)
        assert not result.passed
        assert "not found" in result.message


def test_fact_check_matches_pattern() -> None:
    """Test fact check with 'matches' when pattern matches."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
requires-python = ">=3.11,<4.0"
""")

        clear_scan_cache()
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Python 3.x", status="confirmed")
        check = FactCheck(matches="python.requires-python", pattern=r">=3\.\d+")

        result = FactRunner().run(ctx, claim, check)
        assert result.passed
        assert result.passed


def test_fact_check_matches_no_match() -> None:
    """Test fact check with 'matches' when pattern doesn't match."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
requires-python = ">=3.11"
""")

        clear_scan_cache()
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Python 4+", status="confirmed")
        check = FactCheck(matches="python.requires-python", pattern=r">=4\.\d+")

        result = FactRunner().run(ctx, claim, check)
        assert not result.passed
        assert "doesn't match" in result.message


def test_fact_check_matches_missing() -> None:
    """Test fact check with 'matches' when fact is missing."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        clear_scan_cache()
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = FactCheck(matches="missing.fact", pattern=".*")

        result = FactRunner().run(ctx, claim, check)
        assert not result.passed
        assert "not found" in result.message


def test_fact_check_no_criteria() -> None:
    """Test fact check with no criteria specified."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        clear_scan_cache()
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = FactCheck()

        result = FactRunner().run(ctx, claim, check)
        assert not result.passed
        assert "no criteria" in result.message


def test_fact_check_empty_fails_when_not_empty() -> None:
    """Test fact check with 'empty' when fact is not empty."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create uv.lock so uses.uv is truthy
        (root / "uv.lock").write_text("")

        clear_scan_cache()
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="No uv", status="confirmed")
        check = FactCheck(empty="uses.uv")

        result = FactRunner().run(ctx, claim, check)
        assert not result.passed
        assert "not empty" in result.message.lower()


def test_fact_check_has_fact_is_falsy() -> None:
    """Test fact check with 'has' when fact exists but is falsy."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create pyproject.toml without requires-python (so it's falsy)
        (root / "pyproject.toml").write_text("""
[project]
name = "test"
""")

        clear_scan_cache()
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Has requires-python", status="confirmed")
        check = FactCheck(has="python.requires-python")

        result = FactRunner().run(ctx, claim, check)
        assert not result.passed
        assert "falsy" in result.message.lower() or "not found" in result.message.lower()


def test_fact_check_has_fact_is_falsy_empty_string() -> None:
    """Test fact check with 'has' when fact value is empty string."""
    from unittest.mock import patch
    from certo.scan import Fact, ScanResult

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        mock_result = ScanResult(facts=[
            Fact(key="test.empty", value="", source="mock")
        ])

        with patch("certo.scan.scan_project", return_value=mock_result):
            clear_scan_cache()
            ctx = CheckContext(
                project_root=root,
                spec_path=root / ".certo" / "spec.toml",
            )
            claim = Claim(id="c-test", text="Has test", status="confirmed")
            check = FactCheck(has="test.empty")

            result = FactRunner().run(ctx, claim, check)
            assert not result.passed
            assert "falsy" in result.message.lower()
