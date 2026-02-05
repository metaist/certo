"""Tests for certo.kb.python_stdlib module."""

from __future__ import annotations

from certo.kb.python_stdlib import (
    get_min_python_version,
    is_module_removed,
    load_stdlib_versions,
    parse_versions_file,
)


def test_parse_versions_file_basic() -> None:
    """Test parsing basic VERSIONS format."""
    content = """
# Comment line
tomllib: 3.11-
asynchat: 2.7-3.11
"""
    modules = parse_versions_file(content)

    assert "tomllib" in modules
    assert modules["tomllib"].added == "3.11"
    assert modules["tomllib"].removed is None

    assert "asynchat" in modules
    assert modules["asynchat"].added == "2.7"
    assert modules["asynchat"].removed == "3.11"


def test_parse_versions_file_empty_lines() -> None:
    """Test that empty lines are skipped."""
    content = """

tomllib: 3.11-

"""
    modules = parse_versions_file(content)
    assert len(modules) == 1
    assert "tomllib" in modules


def test_parse_versions_file_no_colon() -> None:
    """Test that lines without colons are skipped."""
    content = """
tomllib: 3.11-
invalid line without colon
pathlib: 3.4-
"""
    modules = parse_versions_file(content)
    assert len(modules) == 2


def test_parse_versions_file_version_without_dash() -> None:
    """Test parsing version without dash (edge case)."""
    content = "oddmodule: 3.5"
    modules = parse_versions_file(content)
    assert modules["oddmodule"].added == "3.5"
    assert modules["oddmodule"].removed is None


def test_load_stdlib_versions() -> None:
    """Test loading bundled typeshed data."""
    versions = load_stdlib_versions()

    # Check some known modules
    assert "tomllib" in versions
    assert versions["tomllib"].added == "3.11"

    assert "pathlib" in versions
    assert versions["pathlib"].added == "3.4"

    # Check a removed module
    assert "distutils" in versions
    assert versions["distutils"].removed is not None


def test_get_min_python_version() -> None:
    """Test getting minimum Python version for a module."""
    assert get_min_python_version("tomllib") == "3.11"
    assert get_min_python_version("pathlib") == "3.4"
    assert get_min_python_version("nonexistent_module") is None


def test_is_module_removed() -> None:
    """Test checking if module is removed.

    Typeshed VERSIONS uses "last version available" format:
    distutils: 3.0-3.11 means distutils exists in 3.11 but NOT in 3.12+
    """
    # tomllib is not removed (no end version)
    assert is_module_removed("tomllib", "3.14") is False

    # nonexistent module
    assert is_module_removed("nonexistent", "3.14") is False

    # distutils: 3.0-3.11 (last available in 3.11)
    assert is_module_removed("distutils", "3.11") is False  # Still available
    assert is_module_removed("distutils", "3.12") is True  # Removed
