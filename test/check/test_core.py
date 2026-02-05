"""Tests for certo.check.core module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.check import check_blueprint


def test_check_blueprint_integration() -> None:
    """Test full blueprint check integration."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        results = check_blueprint(blueprint)
        assert len(results) == 1
        assert results[0].passed


def test_check_blueprint_missing() -> None:
    """Test full check on missing blueprint."""
    results = check_blueprint(Path("/nonexistent/.certo/spec.toml"))
    assert len(results) == 1
    assert not results[0].passed


def test_check_blueprint_skips_static_concerns() -> None:
    """Test that static concerns without handlers are skipped."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-static"
claim = "Some static check"
strategy = "static"
""")

        results = check_blueprint(blueprint)
        # Should only have c1 (TOML valid), not the static concern
        assert len(results) == 1
        assert results[0].concern_id == "c1"


def test_check_blueprint_auto_strategy_with_context() -> None:
    """Test auto strategy with context uses LLM."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-test"
claim = "Test claim"
strategy = "auto"
context = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        # Auto with context should try LLM, but offline so skipped
        results = check_blueprint(blueprint, offline=True)
        assert len(results) == 2
        assert results[1].concern_id == "c-test"
        assert "skipped" in results[1].message.lower()


def test_check_blueprint_auto_strategy_without_context() -> None:
    """Test auto strategy without context is skipped."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-auto-no-context"
claim = "Test claim without context"
strategy = "auto"
""")

        # Auto without context should be silently skipped
        results = check_blueprint(blueprint)
        # Should only have c1 (TOML valid), not the auto concern
        assert len(results) == 1
        assert results[0].concern_id == "c1"
