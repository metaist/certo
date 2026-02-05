"""Tests for certo.check.static module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.check import CheckContext
from certo.check.static import check_spec_exists, check_spec_valid_toml


def _make_ctx(spec_path: Path) -> CheckContext:
    """Create a CheckContext for testing."""
    return CheckContext(
        project_root=spec_path.parent,
        spec_path=spec_path,
    )


def test_check_spec_exists_success() -> None:
    """Test that existing spec is detected."""
    with TemporaryDirectory() as tmpdir:
        spec = Path(tmpdir) / "spec.toml"
        spec.write_text('[spec]\nname = "test"\nversion = 1\n')

        ctx = _make_ctx(spec)
        result = check_spec_exists(ctx)
        assert result.passed
        assert result.claim_id == "builtin-spec-exists"


def test_check_spec_exists_failure() -> None:
    """Test that missing spec is detected."""
    ctx = _make_ctx(Path("/nonexistent/spec.toml"))
    result = check_spec_exists(ctx)
    assert not result.passed
    assert "not found" in result.message.lower()


def test_check_spec_valid_toml_success() -> None:
    """Test that valid TOML is accepted."""
    with TemporaryDirectory() as tmpdir:
        spec = Path(tmpdir) / "spec.toml"
        spec.write_text('[spec]\nname = "test"\nversion = 1\n')

        ctx = _make_ctx(spec)
        result = check_spec_valid_toml(ctx)
        assert result.passed
        assert result.strategy == "static"


def test_check_spec_valid_toml_failure() -> None:
    """Test that invalid TOML is rejected."""
    with TemporaryDirectory() as tmpdir:
        spec = Path(tmpdir) / "spec.toml"
        spec.write_text("this is not valid toml [[[")

        ctx = _make_ctx(spec)
        result = check_spec_valid_toml(ctx)
        assert not result.passed
        assert "invalid toml" in result.message.lower()


def test_check_spec_valid_toml_missing_file() -> None:
    """Test TOML check on missing file."""
    ctx = _make_ctx(Path("/nonexistent/spec.toml"))
    result = check_spec_valid_toml(ctx)
    assert not result.passed
    assert "does not exist" in result.message.lower()
