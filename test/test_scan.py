"""Tests for certo.scan module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.scan import (
    check_consistency,
    extract_classifiers_versions,
    parse_ci_workflows,
    parse_pyproject,
    parse_requires_python,
    parse_version_tuple,
    scan_imports,
    scan_project,
    PythonVersionInfo,
)


def test_parse_version_tuple() -> None:
    """Test parsing version strings."""
    assert parse_version_tuple("3.11") == (3, 11)
    assert parse_version_tuple("3.9") == (3, 9)


def test_parse_requires_python() -> None:
    """Test parsing requires-python specs."""
    assert parse_requires_python(">=3.11") == ((3, 11), None)
    assert parse_requires_python(">=3.11,<3.15") == ((3, 11), (3, 15))
    assert parse_requires_python("<3.12") == (None, (3, 12))


def test_extract_classifiers_versions() -> None:
    """Test extracting versions from classifiers."""
    classifiers = [
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
    ]
    assert extract_classifiers_versions(classifiers) == ["3.11", "3.12"]


def test_parse_pyproject() -> None:
    """Test parsing pyproject.toml."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            """
[project]
requires-python = ">=3.11,<3.15"
classifiers = [
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
"""
        )

        info = parse_pyproject(root)
        assert info.requires_python == ">=3.11,<3.15"
        assert info.min_version == (3, 11)
        assert info.max_version == (3, 15)
        assert info.classifiers == ["3.11", "3.12"]


def test_parse_pyproject_missing() -> None:
    """Test parsing when pyproject.toml doesn't exist."""
    with TemporaryDirectory() as tmpdir:
        info = parse_pyproject(Path(tmpdir))
        assert info.requires_python is None


def test_parse_ci_workflows() -> None:
    """Test parsing CI workflow files."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        ci = workflows / "ci.yaml"
        ci.write_text(
            """
jobs:
  build:
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
"""
        )

        versions = parse_ci_workflows(root)
        assert versions == ["3.11", "3.12", "3.13"]


def test_parse_ci_workflows_missing() -> None:
    """Test parsing when no workflows exist."""
    with TemporaryDirectory() as tmpdir:
        versions = parse_ci_workflows(Path(tmpdir))
        assert versions == []


def test_scan_imports() -> None:
    """Test scanning imports for version requirements."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        src.mkdir()
        module = src / "test.py"
        module.write_text("import tomllib\n")

        min_ver, evidence = scan_imports(root)
        assert min_ver == (3, 11)
        assert len(evidence) == 1
        assert "tomllib" in evidence[0]


def test_scan_imports_no_src() -> None:
    """Test scanning when no src directory."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module = root / "test.py"
        module.write_text("import dataclasses\n")

        min_ver, evidence = scan_imports(root)
        assert min_ver == (3, 7)


def test_check_consistency_ci_mismatch() -> None:
    """Test detecting CI version mismatch."""
    info = PythonVersionInfo(
        requires_python=">=3.11",
        min_version=(3, 11),
        ci_versions=["3.10", "3.11"],
    )

    issues = check_consistency(info)
    assert len(issues) == 1
    assert "3.10" in issues[0].message
    assert issues[0].severity == "error"


def test_check_consistency_import_mismatch() -> None:
    """Test detecting import version mismatch."""
    info = PythonVersionInfo(
        requires_python=">=3.9",
        min_version=(3, 9),
        import_min_version=(3, 11),
    )

    issues = check_consistency(info)
    assert len(issues) == 1
    assert "3.11" in issues[0].message


def test_check_consistency_no_issues() -> None:
    """Test when everything is consistent."""
    info = PythonVersionInfo(
        requires_python=">=3.11",
        min_version=(3, 11),
        ci_versions=["3.11", "3.12"],
        classifiers=["3.11", "3.12"],
        import_min_version=(3, 11),
    )

    issues = check_consistency(info)
    assert len(issues) == 0


def test_scan_project_integration() -> None:
    """Test full project scan."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create pyproject.toml
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            """
[project]
requires-python = ">=3.11"
classifiers = ["Programming Language :: Python :: 3.11"]
"""
        )

        # Create source file
        src = root / "src"
        src.mkdir()
        module = src / "app.py"
        module.write_text("import tomllib\n")

        # Create CI workflow
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        ci = workflows / "ci.yaml"
        ci.write_text('python-version: ["3.11"]\n')

        result = scan_project(root)
        assert len(result.assumptions) == 1
        assert result.assumptions[0].status == "verified"
        assert len(result.issues) == 0


def test_scan_project_with_issues() -> None:
    """Test project scan that finds issues."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        pyproject = root / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')

        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        ci = workflows / "ci.yaml"
        ci.write_text('python-version: ["3.10", "3.11"]\n')

        result = scan_project(root)
        assert len(result.issues) == 1
        assert result.assumptions[0].status == "violated"


def test_scan_project_no_pyproject() -> None:
    """Test project scan with no pyproject.toml."""
    with TemporaryDirectory() as tmpdir:
        result = scan_project(Path(tmpdir))
        assert len(result.assumptions) == 0
        assert len(result.issues) == 0


def test_check_consistency_classifier_mismatch() -> None:
    """Test detecting classifier version mismatch."""
    info = PythonVersionInfo(
        requires_python=">=3.11",
        min_version=(3, 11),
        classifiers=["3.9", "3.10", "3.11"],
    )

    issues = check_consistency(info)
    # Should warn about 3.9 and 3.10
    assert len(issues) == 2
    assert all(i.severity == "warning" for i in issues)


def test_check_consistency_max_version() -> None:
    """Test detecting CI version above max."""
    info = PythonVersionInfo(
        requires_python=">=3.11,<3.14",
        min_version=(3, 11),
        max_version=(3, 14),
        ci_versions=["3.11", "3.14"],
    )

    issues = check_consistency(info)
    assert len(issues) == 1
    assert "3.14" in issues[0].message


def test_parse_ci_workflows_invalid_yaml() -> None:
    """Test parsing invalid workflow file."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        ci = workflows / "ci.yaml"
        # Create a file that will fail to parse but not crash
        ci.write_text("not a valid yaml with python-version")

        versions = parse_ci_workflows(root)
        # Should return empty list, not crash
        assert versions == []


def test_scan_imports_invalid_python() -> None:
    """Test scanning file with invalid Python syntax."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        src.mkdir()
        module = src / "bad.py"
        module.write_text("this is not valid python {{{\n")

        # Should not crash, just skip the file
        min_ver, evidence = scan_imports(root)
        assert min_ver is None
        assert evidence == []


def test_check_consistency_no_min_version() -> None:
    """Test consistency check with no min version."""
    info = PythonVersionInfo()
    issues = check_consistency(info)
    assert len(issues) == 0


def test_scan_imports_import_from_no_module() -> None:
    """Test scanning 'from . import x' style imports."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        src.mkdir()
        module = src / "test.py"
        # This is a relative import with no module name
        module.write_text("from . import something\nimport tomllib\n")

        min_ver, evidence = scan_imports(root)
        assert min_ver == (3, 11)
        # Should still find tomllib
        assert any("tomllib" in e for e in evidence)


def test_parse_ci_workflows_exception() -> None:
    """Test handling exception when reading workflow file."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        # Create a directory named ci.yaml to cause read error
        ci = workflows / "ci.yaml"
        ci.mkdir()

        versions = parse_ci_workflows(root)
        assert versions == []
