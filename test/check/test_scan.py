"""Tests for certo.check.scan module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.check import check_spec


def test_check_spec_scan_strategy_pass() -> None:
    """Test scan strategy that passes."""
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
id = "c-scan"
text = "Python versions are consistent"
status = "confirmed"
verify = ["scan"]
""")
        # Create pyproject.toml with requires-python
        (root / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')

        results = check_spec(spec)
        assert len(results) == 2  # builtin + c-scan
        assert results[1].claim_id == "c-scan"
        assert results[1].passed
        assert results[1].strategy == "scan"


def test_check_spec_scan_strategy_no_assumptions() -> None:
    """Test scan strategy with no assumptions."""
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
id = "c-scan"
text = "Python versions are consistent"
status = "confirmed"
verify = ["scan"]
""")
        # No pyproject.toml, so scan finds nothing

        results = check_spec(spec)
        assert len(results) == 2
        assert results[1].claim_id == "c-scan"
        assert results[1].passed
        assert "no issues" in results[1].message.lower()


def test_check_spec_scan_strategy_fail() -> None:
    """Test scan strategy that fails."""
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
id = "c-scan"
text = "Python versions are consistent"
status = "confirmed"
verify = ["scan"]
""")
        # Create inconsistent versions
        (root / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yaml").write_text('python-version: ["3.9", "3.10"]\n')

        results = check_spec(spec)
        assert len(results) == 2
        assert results[1].claim_id == "c-scan"
        assert not results[1].passed
        assert "issues" in results[1].message.lower()
