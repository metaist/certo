"""Tests for certo.check.static module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.check import CheckContext
from certo.check.static import check_blueprint_exists, check_blueprint_valid_toml


def _make_ctx(blueprint_path: Path) -> CheckContext:
    """Create a CheckContext for testing."""
    return CheckContext(
        project_root=blueprint_path.parent,
        blueprint_path=blueprint_path,
    )


def test_check_blueprint_exists_success() -> None:
    """Test that existing blueprint is detected."""
    with TemporaryDirectory() as tmpdir:
        blueprint = Path(tmpdir) / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        ctx = _make_ctx(blueprint)
        result = check_blueprint_exists(ctx)
        assert result.passed
        assert result.concern_id == "c1"


def test_check_blueprint_exists_failure() -> None:
    """Test that missing blueprint is detected."""
    ctx = _make_ctx(Path("/nonexistent/blueprint.toml"))
    result = check_blueprint_exists(ctx)
    assert not result.passed
    assert "not found" in result.message.lower()


def test_check_blueprint_valid_toml_success() -> None:
    """Test that valid TOML is accepted."""
    with TemporaryDirectory() as tmpdir:
        blueprint = Path(tmpdir) / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\nversion = "0.1.0"\n')

        ctx = _make_ctx(blueprint)
        result = check_blueprint_valid_toml(ctx)
        assert result.passed
        assert result.strategy == "static"


def test_check_blueprint_valid_toml_failure() -> None:
    """Test that invalid TOML is rejected."""
    with TemporaryDirectory() as tmpdir:
        blueprint = Path(tmpdir) / "blueprint.toml"
        blueprint.write_text("this is not valid toml [[[")

        ctx = _make_ctx(blueprint)
        result = check_blueprint_valid_toml(ctx)
        assert not result.passed
        assert "invalid toml" in result.message.lower()


def test_check_blueprint_valid_toml_missing_file() -> None:
    """Test TOML check on missing file."""
    ctx = _make_ctx(Path("/nonexistent/blueprint.toml"))
    result = check_blueprint_valid_toml(ctx)
    assert not result.passed
    assert "does not exist" in result.message.lower()
