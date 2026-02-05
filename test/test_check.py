"""Tests for certo.check module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.check import (
    check_blueprint,
    check_blueprint_exists,
    check_blueprint_valid_toml,
)


def test_check_blueprint_exists_success() -> None:
    """Test that existing blueprint is detected."""
    with TemporaryDirectory() as tmpdir:
        blueprint = Path(tmpdir) / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        result = check_blueprint_exists(blueprint)
        assert result.passed
        assert result.concern_id == "c1"


def test_check_blueprint_exists_failure() -> None:
    """Test that missing blueprint is detected."""
    result = check_blueprint_exists(Path("/nonexistent/blueprint.toml"))
    assert not result.passed
    assert "not found" in result.message.lower()


def test_check_blueprint_valid_toml_success() -> None:
    """Test that valid TOML is accepted."""
    with TemporaryDirectory() as tmpdir:
        blueprint = Path(tmpdir) / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\nversion = "0.1.0"\n')

        result = check_blueprint_valid_toml(blueprint)
        assert result.passed
        assert result.strategy == "static"


def test_check_blueprint_valid_toml_failure() -> None:
    """Test that invalid TOML is rejected."""
    with TemporaryDirectory() as tmpdir:
        blueprint = Path(tmpdir) / "blueprint.toml"
        blueprint.write_text("this is not valid toml [[[")

        result = check_blueprint_valid_toml(blueprint)
        assert not result.passed
        assert "invalid toml" in result.message.lower()


def test_check_blueprint_valid_toml_missing_file() -> None:
    """Test TOML check on missing file."""
    result = check_blueprint_valid_toml(Path("/nonexistent/blueprint.toml"))
    assert not result.passed
    assert "does not exist" in result.message.lower()


def test_check_blueprint_integration() -> None:
    """Test full blueprint check integration."""
    with TemporaryDirectory() as tmpdir:
        blueprint = Path(tmpdir) / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        results = check_blueprint(blueprint)
        assert len(results) == 1
        assert results[0].passed


def test_check_blueprint_missing() -> None:
    """Test full check on missing blueprint."""
    results = check_blueprint(Path("/nonexistent/blueprint.toml"))
    assert len(results) == 1
    assert not results[0].passed
