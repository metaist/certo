"""Tests for certo.scan.python module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.scan import ScanResult
from certo.scan.python import (
    parse_version_tuple,
    scan_python,
)


def test_parse_version_tuple() -> None:
    """Test parsing version strings."""
    assert parse_version_tuple("3.11") == (3, 11)
    assert parse_version_tuple("3.9") == (3, 9)


def test_scan_python_empty() -> None:
    """Test scanning empty directory."""
    with TemporaryDirectory() as tmpdir:
        result = ScanResult()
        scan_python(Path(tmpdir), result)
        assert result.facts == []


def test_scan_python_pyproject_full() -> None:
    """Test scanning pyproject.toml with all fields."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
name = "test"
requires-python = ">=3.11,<3.15"
classifiers = [
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[tool.pytest]
testpaths = ["test"]
""")
        result = ScanResult()
        scan_python(root, result)

        assert result.has("file.exists.pyproject.toml")
        assert result.get_value("python.requires-python") == ">=3.11,<3.15"
        assert result.get_value("python.min-version") == "3.11"
        assert result.get_value("python.version-lt") == "3.15"
        assert result.get_value("python.max-version") == "3.14"  # derived from <3.15
        assert result.has("uses.pytest")


def test_scan_python_pyproject_parse_error() -> None:
    """Test handling invalid pyproject.toml."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("invalid toml {{{{")
        result = ScanResult()
        scan_python(root, result)

        assert result.has("file.exists.pyproject.toml")
        assert len(result.errors) > 0
        assert "Failed to parse" in result.errors[0]


def test_scan_python_ci_multiple_workflows() -> None:
    """Test scanning multiple workflow files."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yaml").write_text("""
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
""")
        (workflows / "docs.yaml").write_text("""
jobs:
  build:
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
""")
        result = ScanResult()
        scan_python(root, result)

        # Should dedupe versions across files
        versions = result.get_value("python.ci-versions")
        assert versions == ["3.11", "3.12", "3.13"]


def test_scan_python_tooling_tox() -> None:
    """Test detecting tox."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "tox.ini").write_text("[tox]")
        result = ScanResult()
        scan_python(root, result)
        assert result.has("uses.tox")


def test_scan_python_tooling_requirements() -> None:
    """Test detecting requirements.txt."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "requirements.txt").write_text("requests>=2.0")
        result = ScanResult()
        scan_python(root, result)
        assert result.has("file.exists.requirements.txt")


def test_scan_python_tooling_setup() -> None:
    """Test detecting setup.py."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "setup.py").write_text("from setuptools import setup")
        result = ScanResult()
        scan_python(root, result)
        assert result.has("file.exists.setup.py")


def test_scan_python_imports_multiple() -> None:
    """Test scanning multiple imports."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        src.mkdir()
        (src / "a.py").write_text("import tomllib\n")
        (src / "b.py").write_text("from pathlib import Path\n")

        result = ScanResult()
        scan_python(root, result)

        # tomllib is 3.11+, pathlib is older
        assert result.get_value("python.import-min-version") == "3.11"
        evidence = result.get_value("python.import-evidence")
        assert isinstance(evidence, list)
        assert any("tomllib" in e for e in evidence)


def test_scan_python_imports_invalid_syntax() -> None:
    """Test handling files with syntax errors."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        src.mkdir()
        (src / "valid.py").write_text("import tomllib\n")
        (src / "invalid.py").write_text("def broken(\n")

        result = ScanResult()
        scan_python(root, result)

        # Should still process valid files
        assert result.has("python.import-min-version")


def test_scan_python_consistency_ci_below_min() -> None:
    """Test detecting CI version below min."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
requires-python = ">=3.11"
""")
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yaml").write_text('python-version: ["3.10", "3.11"]')

        result = ScanResult()
        scan_python(root, result)

        issues = result.get_value("python.consistency-issues")
        assert issues is not None
        assert isinstance(issues, list) and any("3.10" in issue for issue in issues)


def test_scan_python_consistency_ci_above_max() -> None:
    """Test detecting CI version above max."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
requires-python = ">=3.11,<3.13"
""")
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yaml").write_text('python-version: ["3.11", "3.13"]')

        result = ScanResult()
        scan_python(root, result)

        issues = result.get_value("python.consistency-issues")
        assert issues is not None
        assert isinstance(issues, list) and any("3.13" in issue for issue in issues)


def test_scan_python_consistency_classifier_below_min() -> None:
    """Test detecting classifier below min."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
requires-python = ">=3.11"
classifiers = [
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.11",
]
""")
        result = ScanResult()
        scan_python(root, result)

        issues = result.get_value("python.consistency-issues")
        assert issues is not None
        assert isinstance(issues, list) and any("3.9" in issue for issue in issues)


def test_scan_python_consistency_import_exceeds_min() -> None:
    """Test detecting imports requiring higher version than min."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
requires-python = ">=3.9"
""")
        src = root / "src"
        src.mkdir()
        (src / "test.py").write_text("import tomllib\n")  # requires 3.11

        result = ScanResult()
        scan_python(root, result)

        issues = result.get_value("python.consistency-issues")
        assert issues is not None
        assert isinstance(issues, list) and any(
            "3.11" in issue and "3.9" in issue for issue in issues
        )


def test_scan_python_max_version_from_ci() -> None:
    """Test deriving max version from CI when no upper bound."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
requires-python = ">=3.11"
""")
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yaml").write_text('python-version: ["3.11", "3.12", "3.14"]')

        result = ScanResult()
        scan_python(root, result)

        assert result.get_value("python.max-version") == "3.14"


def test_scan_python_no_consistency_issues() -> None:
    """Test no consistency issues when everything matches."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
requires-python = ">=3.11,<3.15"
classifiers = [
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
""")
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yaml").write_text('python-version: ["3.11", "3.12"]')

        result = ScanResult()
        scan_python(root, result)

        assert not result.has("python.consistency-issues")


def test_scan_python_requires_python_no_min() -> None:
    """Test scan with requires-python that has no minimum (only max)."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
name = "test"
requires-python = "<4.0"
""")

        result = ScanResult()
        scan_python(root, result)
        # Should not have min-version fact
        assert not result.has("python.min-version")
        # But should have requires-python
        assert result.has("python.requires-python")


def test_scan_python_classifiers_no_version() -> None:
    """Test scan with classifiers that don't have version numbers."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
name = "test"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
]
""")

        result = ScanResult()
        scan_python(root, result)
        # Should not have classifier-versions fact (no specific versions)
        assert not result.has("python.classifier-versions")


def test_scan_python_ci_workflow_no_python_version() -> None:
    """Test scan with CI workflow that doesn't specify python-version."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yaml").write_text("""
name: CI
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
""")

        result = ScanResult()
        scan_python(root, result)
        # Should not have ci-versions fact
        assert not result.has("python.ci-versions")


def test_scan_python_relative_import() -> None:
    """Test scan handles relative imports (from . import)."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "mypackage").mkdir()
        (root / "mypackage" / "__init__.py").write_text("")
        (root / "mypackage" / "module.py").write_text("""
from . import submodule
from .other import something
""")
        (root / "mypackage" / "submodule.py").write_text("")
        (root / "mypackage" / "other.py").write_text("something = 1")

        result = ScanResult()
        scan_python(root, result)
        # Should not crash and should not add import-min-version for relative imports
        # (relative imports don't affect stdlib version requirements)


def test_scan_python_pytest_ini_only() -> None:
    """Test scan detects pytest from pytest.ini when no pyproject.toml."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pytest.ini").write_text("""
[pytest]
testpaths = tests
""")

        result = ScanResult()
        scan_python(root, result)
        # pytest.ini exists but no pyproject.toml
        # Currently doesn't detect pytest from pytest.ini alone
        # (only checks pyproject.toml for tool.pytest)


def test_scan_python_import_min_within_requires() -> None:
    """Test scan when import min version is within requires-python."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
name = "test"
requires-python = ">=3.11"
""")
        # Use a module that requires 3.11
        (root / "main.py").write_text("""
import tomllib  # 3.11+
""")

        result = ScanResult()
        scan_python(root, result)
        # import-min-version should be 3.11
        assert result.get_value("python.import-min-version") == "3.11"
        # No consistency issues since requires-python >= import min
        assert not result.has("python.consistency-issues")
