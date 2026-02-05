"""Tests for certo.check.scan module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.check import check_blueprint


def test_check_blueprint_scan_strategy_pass() -> None:
    """Test static strategy with verify_with=['scan'] that passes."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-scan"
claim = "Python versions are consistent"
strategy = "static"
verify_with = ["scan"]
""")
        # Create pyproject.toml with requires-python
        (root / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')

        results = check_blueprint(blueprint)
        assert len(results) == 2  # c1 + c-scan
        assert results[1].concern_id == "c-scan"
        assert results[1].passed
        assert results[1].strategy == "scan"


def test_check_blueprint_scan_strategy_no_assumptions() -> None:
    """Test static strategy with verify_with=['scan'] with no assumptions."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-scan"
claim = "Python versions are consistent"
strategy = "static"
verify_with = ["scan"]
""")
        # No pyproject.toml, so scan finds nothing

        results = check_blueprint(blueprint)
        assert len(results) == 2
        assert results[1].concern_id == "c-scan"
        assert results[1].passed
        assert "no issues" in results[1].message.lower()


def test_check_blueprint_scan_strategy_fail() -> None:
    """Test static strategy with verify_with=['scan'] that fails."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-scan"
claim = "Python versions are consistent"
strategy = "static"
verify_with = ["scan"]
""")
        # Create inconsistent versions
        (root / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yaml").write_text('python-version: ["3.9", "3.10"]\n')

        results = check_blueprint(blueprint)
        assert len(results) == 2
        assert results[1].concern_id == "c-scan"
        assert not results[1].passed
        assert "issues" in results[1].message.lower()
