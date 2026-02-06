"""Tests for certo.scan module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.scan import Fact, ScanResult, scan_project


def test_fact_dataclass() -> None:
    """Test Fact dataclass."""
    fact = Fact(key="test.key", value="test-value", source="test.txt")
    assert fact.key == "test.key"
    assert fact.value == "test-value"
    assert fact.source == "test.txt"
    assert fact.confidence == 1.0


def test_scan_result_get() -> None:
    """Test ScanResult.get() method."""
    result = ScanResult(
        facts=[
            Fact(key="foo", value="bar", source="test"),
            Fact(key="baz", value=True, source="test"),
        ]
    )
    assert result.get("foo") is not None
    assert result.get("foo").value == "bar"  # type: ignore[union-attr]
    assert result.get("missing") is None


def test_scan_result_has() -> None:
    """Test ScanResult.has() method."""
    result = ScanResult(
        facts=[
            Fact(key="truthy.str", value="yes", source="test"),
            Fact(key="truthy.bool", value=True, source="test"),
            Fact(key="truthy.list", value=["a", "b"], source="test"),
            Fact(key="falsy.str", value="", source="test"),
            Fact(key="falsy.bool", value=False, source="test"),
            Fact(key="falsy.list", value=[], source="test"),
        ]
    )
    assert result.has("truthy.str")
    assert result.has("truthy.bool")
    assert result.has("truthy.list")
    assert not result.has("falsy.str")
    assert not result.has("falsy.bool")
    assert not result.has("falsy.list")
    assert not result.has("missing")


def test_scan_result_get_value() -> None:
    """Test ScanResult.get_value() method."""
    result = ScanResult(facts=[Fact(key="foo", value="bar", source="test")])
    assert result.get_value("foo") == "bar"
    assert result.get_value("missing") is None
    assert result.get_value("missing", "default") == "default"


def test_scan_result_filter() -> None:
    """Test ScanResult.filter() method."""
    result = ScanResult(
        facts=[
            Fact(key="python.version", value="3.11", source="test"),
            Fact(key="python.min", value="3.9", source="test"),
            Fact(key="uses.uv", value=True, source="test"),
        ]
    )
    python_facts = result.filter("python.")
    assert len(python_facts) == 2
    assert all(f.key.startswith("python.") for f in python_facts)


def test_scan_project_empty() -> None:
    """Test scanning an empty directory."""
    with TemporaryDirectory() as tmpdir:
        result = scan_project(Path(tmpdir))
        assert result.facts == []
        assert result.errors == []


def test_scan_project_with_pyproject() -> None:
    """Test scanning a project with pyproject.toml."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text("""
[project]
name = "test-project"
requires-python = ">=3.11"
classifiers = [
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
""")
        result = scan_project(root)

        assert result.has("file.exists.pyproject.toml")
        assert result.get_value("python.min-version") == "3.11"
        assert result.get_value("project.name") == "test-project"
        assert result.get_value("python.classifier-versions") == ["3.11", "3.12"]


def test_scan_project_with_ci() -> None:
    """Test scanning a project with GitHub Actions."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yaml").write_text("""
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
""")
        result = scan_project(root)

        assert result.has("uses.github-actions")
        assert result.get_value("python.ci-versions") == ["3.11", "3.12", "3.13"]


def test_scan_project_with_tooling() -> None:
    """Test scanning for Python tooling."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "uv.lock").write_text("")
        result = scan_project(root)
        assert result.has("uses.uv")


def test_scan_project_with_poetry() -> None:
    """Test scanning for Poetry."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "poetry.lock").write_text("")
        result = scan_project(root)
        assert result.has("uses.poetry")


def test_scan_project_with_imports() -> None:
    """Test scanning Python imports."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        src.mkdir()
        (src / "test.py").write_text("import tomllib\n")

        result = scan_project(root)

        assert result.has("python.import-min-version")
        # tomllib requires Python 3.11+
        assert result.get_value("python.import-min-version") == "3.11"
