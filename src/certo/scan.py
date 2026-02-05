"""Scan project files to discover assumptions and check consistency."""

from __future__ import annotations

import ast
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# Known stdlib modules and their introduction versions
STDLIB_VERSIONS: dict[str, str] = {
    "tomllib": "3.11",
    "importlib.metadata": "3.8",
    "dataclasses": "3.7",
    "typing": "3.5",
    "pathlib": "3.4",
    "asyncio": "3.4",
    "enum": "3.4",
    "statistics": "3.4",
    "contextvars": "3.7",
    "graphlib": "3.9",
    "zoneinfo": "3.9",
}


@dataclass
class PythonVersionInfo:
    """Information about Python version requirements."""

    requires_python: str | None = None
    min_version: tuple[int, int] | None = None
    max_version: tuple[int, int] | None = None
    classifiers: list[str] = field(default_factory=list)
    ci_versions: list[str] = field(default_factory=list)
    import_min_version: tuple[int, int] | None = None
    import_evidence: list[str] = field(default_factory=list)


@dataclass
class Assumption:
    """A discovered assumption about the project."""

    id: str
    description: str
    category: str
    evidence: list[str]
    should_match: list[str]
    status: str  # "verified" | "unverified" | "violated"


@dataclass
class ConsistencyIssue:
    """An inconsistency between sources of truth."""

    message: str
    sources: list[str]
    severity: str  # "error" | "warning"


@dataclass
class ScanResult:
    """Result of scanning the project."""

    assumptions: list[Assumption]
    issues: list[ConsistencyIssue]
    python_info: PythonVersionInfo


def parse_version_tuple(version_str: str) -> tuple[int, int]:
    """Parse '3.11' into (3, 11)."""
    parts = version_str.split(".")
    return (int(parts[0]), int(parts[1]))


def parse_requires_python(
    spec: str,
) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    """Parse requires-python spec into (min, max) version tuples."""
    min_ver = None
    max_ver = None

    # Handle common patterns
    # >=3.11 or >=3.11,<3.15
    ge_match = re.search(r">=\s*(\d+\.\d+)", spec)
    if ge_match:
        min_ver = parse_version_tuple(ge_match.group(1))

    lt_match = re.search(r"<\s*(\d+\.\d+)", spec)
    if lt_match:
        max_ver = parse_version_tuple(lt_match.group(1))

    return min_ver, max_ver


def extract_classifiers_versions(classifiers: list[str]) -> list[str]:
    """Extract Python versions from classifiers."""
    versions = []
    for c in classifiers:
        match = re.match(r"Programming Language :: Python :: (\d+\.\d+)$", c)
        if match:
            versions.append(match.group(1))
    return sorted(versions)


def parse_pyproject(project_root: Path) -> PythonVersionInfo:
    """Parse pyproject.toml for Python version info."""
    info = PythonVersionInfo()
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        return info

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})

    # requires-python
    if "requires-python" in project:
        requires_python: str = project["requires-python"]
        info.requires_python = requires_python
        info.min_version, info.max_version = parse_requires_python(requires_python)

    # classifiers
    if "classifiers" in project:
        info.classifiers = extract_classifiers_versions(project["classifiers"])

    return info


def parse_ci_workflows(project_root: Path) -> list[str]:
    """Parse GitHub Actions workflows for Python versions in matrix."""
    versions: set[str] = set()
    workflows_dir = project_root / ".github" / "workflows"

    if not workflows_dir.exists():
        return []

    for workflow_file in workflows_dir.glob("*.yaml"):
        try:
            # Simple YAML parsing for python-version matrix
            content = workflow_file.read_text()
            # Look for python-version: ["3.11", "3.12", ...]
            match = re.search(r"python-version:\s*\[(.*?)\]", content)
            if match:
                items = match.group(1)
                for v in re.findall(r'"(\d+\.\d+)"', items):
                    versions.add(v)
        except Exception:
            continue

    return sorted(versions)


def scan_imports(project_root: Path) -> tuple[tuple[int, int] | None, list[str]]:
    """Scan Python files for imports that require specific Python versions."""
    min_version: tuple[int, int] | None = None
    evidence: list[str] = []

    src_dir = project_root / "src"
    if not src_dir.exists():
        src_dir = project_root

    for py_file in src_dir.rglob("*.py"):
        try:
            content = py_file.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                module_name = None
                lineno = 0
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split(".")[0]
                    lineno = node.lineno
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split(".")[0]
                    lineno = node.lineno

                if module_name and module_name in STDLIB_VERSIONS:
                    required = STDLIB_VERSIONS[module_name]
                    required_tuple = parse_version_tuple(required)
                    rel_path = py_file.relative_to(project_root)
                    evidence.append(
                        f"{rel_path}:{lineno}: import {module_name} (requires {required}+)"
                    )
                    if min_version is None or required_tuple > min_version:
                        min_version = required_tuple

        except Exception:
            continue

    return min_version, evidence


def check_consistency(info: PythonVersionInfo) -> list[ConsistencyIssue]:
    """Check for inconsistencies between sources of truth."""
    issues: list[ConsistencyIssue] = []

    if info.min_version is None:
        return issues

    min_ver_str = f"{info.min_version[0]}.{info.min_version[1]}"

    # Check CI versions against requires-python
    for ci_ver in info.ci_versions:
        ci_tuple = parse_version_tuple(ci_ver)
        if ci_tuple < info.min_version:
            issues.append(
                ConsistencyIssue(
                    message=f"CI tests Python {ci_ver}, but requires-python is >={min_ver_str}",
                    sources=[
                        "pyproject.toml:requires-python",
                        ".github/workflows/*.yaml",
                    ],
                    severity="error",
                )
            )
        if info.max_version and ci_tuple >= info.max_version:
            max_ver_str = f"{info.max_version[0]}.{info.max_version[1]}"
            issues.append(
                ConsistencyIssue(
                    message=f"CI tests Python {ci_ver}, but requires-python is <{max_ver_str}",
                    sources=[
                        "pyproject.toml:requires-python",
                        ".github/workflows/*.yaml",
                    ],
                    severity="error",
                )
            )

    # Check classifiers against requires-python
    for classifier_ver in info.classifiers:
        ver_tuple = parse_version_tuple(classifier_ver)
        if ver_tuple < info.min_version:
            issues.append(
                ConsistencyIssue(
                    message=f"Classifier lists Python {classifier_ver}, but requires-python is >={min_ver_str}",
                    sources=[
                        "pyproject.toml:classifiers",
                        "pyproject.toml:requires-python",
                    ],
                    severity="warning",
                )
            )

    # Check imports against requires-python
    if info.import_min_version and info.import_min_version > info.min_version:
        import_ver_str = f"{info.import_min_version[0]}.{info.import_min_version[1]}"
        issues.append(
            ConsistencyIssue(
                message=f"Imports require Python {import_ver_str}+, but requires-python is >={min_ver_str}",
                sources=["source imports", "pyproject.toml:requires-python"],
                severity="error",
            )
        )

    return issues


def scan_project(project_root: Path) -> ScanResult:
    """Scan a project and return discovered assumptions and issues."""
    # Gather information
    info = parse_pyproject(project_root)
    info.ci_versions = parse_ci_workflows(project_root)
    info.import_min_version, info.import_evidence = scan_imports(project_root)

    # Check consistency
    issues = check_consistency(info)

    # Build assumptions
    assumptions: list[Assumption] = []

    if info.min_version:
        min_ver_str = f"{info.min_version[0]}.{info.min_version[1]}"
        evidence = [f"pyproject.toml requires-python = '{info.requires_python}'"]
        evidence.extend(info.import_evidence)

        should_match = []
        if info.ci_versions:
            should_match.append(".github/workflows/*.yaml matrix")
        if info.classifiers:
            should_match.append("pyproject.toml classifiers")

        # Determine status
        status = "verified" if not issues else "violated"

        assumptions.append(
            Assumption(
                id="a-python-version",
                description=f"Python {min_ver_str}+ is required",
                category="compatibility",
                evidence=evidence,
                should_match=should_match,
                status=status,
            )
        )

    return ScanResult(
        assumptions=assumptions,
        issues=issues,
        python_info=info,
    )
