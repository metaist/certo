"""Python-specific project scanning."""

from __future__ import annotations

import ast
import re
import tomllib
from functools import lru_cache
from pathlib import Path

from certo.kb.python_stdlib import load_stdlib_versions
from certo.scan import Fact, ScanResult


@lru_cache(maxsize=1)
def get_stdlib_versions() -> dict[str, str]:
    """Get stdlib module versions from knowledge base."""
    versions = load_stdlib_versions()
    return {name: info.added for name, info in versions.items()}


def parse_version_tuple(version_str: str) -> tuple[int, int]:
    """Parse '3.11' into (3, 11)."""
    parts = version_str.split(".")
    return (int(parts[0]), int(parts[1]))


def scan_python(root: Path, result: ScanResult) -> None:
    """Scan for Python-related facts."""
    _scan_pyproject(root, result)
    _scan_ci_workflows(root, result)
    _scan_imports(root, result)
    _scan_tooling(root, result)
    _compute_derived_facts(result)


def _scan_pyproject(root: Path, result: ScanResult) -> None:
    """Scan pyproject.toml for Python facts."""
    pyproject_path = root / "pyproject.toml"

    if not pyproject_path.exists():
        return

    result.facts.append(
        Fact(
            key="file.exists.pyproject.toml",
            value=True,
            source="pyproject.toml",
        )
    )

    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        result.errors.append(f"Failed to parse pyproject.toml: {e}")
        return

    project = data.get("project", {})

    # requires-python
    if "requires-python" in project:
        requires_python: str = project["requires-python"]
        result.facts.append(
            Fact(
                key="python.requires-python",
                value=requires_python,
                source="pyproject.toml:project.requires-python",
            )
        )

        # Parse min/max versions
        ge_match = re.search(r">=\s*(\d+\.\d+)", requires_python)
        if ge_match:
            result.facts.append(
                Fact(
                    key="python.min-version",
                    value=ge_match.group(1),
                    source="pyproject.toml:project.requires-python",
                )
            )

        lt_match = re.search(r"<\s*(\d+\.\d+)", requires_python)
        if lt_match:
            result.facts.append(
                Fact(
                    key="python.version-lt",
                    value=lt_match.group(1),
                    source="pyproject.toml:project.requires-python",
                )
            )
            # Note: python.max-version (the actual max supported) is computed in _compute_derived_facts

    # classifiers
    classifiers = project.get("classifiers", [])
    python_versions = []
    for c in classifiers:
        match = re.match(r"Programming Language :: Python :: (\d+\.\d+)$", c)
        if match:
            python_versions.append(match.group(1))

    if python_versions:
        result.facts.append(
            Fact(
                key="python.classifier-versions",
                value=sorted(python_versions),
                source="pyproject.toml:project.classifiers",
            )
        )

    # Project name
    if "name" in project:
        result.facts.append(
            Fact(
                key="project.name",
                value=project["name"],
                source="pyproject.toml:project.name",
            )
        )


def _scan_ci_workflows(root: Path, result: ScanResult) -> None:
    """Scan GitHub Actions workflows for Python versions."""
    workflows_dir = root / ".github" / "workflows"

    if not workflows_dir.exists():
        return

    result.facts.append(
        Fact(
            key="uses.github-actions",
            value=True,
            source=".github/workflows/",
        )
    )

    versions: set[str] = set()

    for workflow_file in workflows_dir.glob("*.yaml"):
        try:
            content = workflow_file.read_text()
            # Look for python-version: ["3.11", "3.12", ...]
            match = re.search(r"python-version:\s*\[(.*?)\]", content)
            if match:
                items = match.group(1)
                for v in re.findall(r'"(\d+\.\d+)"', items):
                    versions.add(v)
        except Exception:
            continue

    if versions:
        result.facts.append(
            Fact(
                key="python.ci-versions",
                value=sorted(versions),
                source=".github/workflows/*.yaml",
            )
        )


def _scan_imports(root: Path, result: ScanResult) -> None:
    """Scan Python imports for version requirements."""
    src_dir = root / "src"
    if not src_dir.exists():
        src_dir = root

    min_version: tuple[int, int] | None = None
    evidence: list[str] = []
    stdlib_versions = get_stdlib_versions()

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

                if module_name and module_name in stdlib_versions:
                    required = stdlib_versions[module_name]
                    required_tuple = parse_version_tuple(required)
                    rel_path = py_file.relative_to(root)
                    evidence.append(f"{rel_path}:{lineno}:{module_name}:{required}")
                    if min_version is None or required_tuple > min_version:
                        min_version = required_tuple

        except Exception:
            continue

    if min_version:
        result.facts.append(
            Fact(
                key="python.import-min-version",
                value=f"{min_version[0]}.{min_version[1]}",
                source="source imports",
            )
        )

    if evidence:
        result.facts.append(
            Fact(
                key="python.import-evidence",
                value=evidence,
                source="source imports",
            )
        )


def _scan_tooling(root: Path, result: ScanResult) -> None:
    """Scan for Python tooling indicators."""
    # uv
    if (root / "uv.lock").exists():
        result.facts.append(Fact(key="uses.uv", value=True, source="uv.lock"))

    # poetry
    if (root / "poetry.lock").exists():
        result.facts.append(Fact(key="uses.poetry", value=True, source="poetry.lock"))

    # pip/requirements
    if (root / "requirements.txt").exists():
        result.facts.append(
            Fact(
                key="file.exists.requirements.txt",
                value=True,
                source="requirements.txt",
            )
        )

    # setup.py (legacy)
    if (root / "setup.py").exists():
        result.facts.append(
            Fact(key="file.exists.setup.py", value=True, source="setup.py")
        )

    # tox
    if (root / "tox.ini").exists():
        result.facts.append(Fact(key="uses.tox", value=True, source="tox.ini"))

    # pytest
    if (root / "pytest.ini").exists() or (root / "pyproject.toml").exists():
        # Check pyproject.toml for pytest config
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            try:
                with pyproject.open("rb") as f:
                    data = tomllib.load(f)
                if "tool" in data and "pytest" in data["tool"]:
                    result.facts.append(
                        Fact(
                            key="uses.pytest",
                            value=True,
                            source="pyproject.toml:tool.pytest",
                        )
                    )
            except Exception:
                pass


def _compute_derived_facts(result: ScanResult) -> None:
    """Compute derived facts and check consistency."""
    issues: list[str] = []

    # Get raw facts
    min_version = result.get_value("python.min-version")
    version_lt = result.get_value("python.version-lt")
    ci_versions = result.get_value("python.ci-versions")
    classifier_versions = result.get_value("python.classifier-versions")
    import_min = result.get_value("python.import-min-version")

    # Compute max-version (highest supported, not the < bound)
    max_version: str | None = None

    if version_lt:
        # <3.15 means max is 3.14
        lt_tuple = parse_version_tuple(str(version_lt))
        max_tuple = (lt_tuple[0], lt_tuple[1] - 1)
        max_version = f"{max_tuple[0]}.{max_tuple[1]}"
    elif ci_versions and isinstance(ci_versions, list):
        # Use highest CI version
        max_version = max(ci_versions, key=lambda v: parse_version_tuple(v))
    elif classifier_versions and isinstance(classifier_versions, list):
        # Use highest classifier version
        max_version = max(classifier_versions, key=lambda v: parse_version_tuple(v))

    if max_version:
        result.facts.append(
            Fact(
                key="python.max-version",
                value=max_version,
                source="derived",
            )
        )

    # Check consistency: CI versions within range
    if min_version and ci_versions and isinstance(ci_versions, list):
        min_tuple = parse_version_tuple(str(min_version))
        for ci_ver in ci_versions:
            ci_tuple = parse_version_tuple(ci_ver)
            if ci_tuple < min_tuple:
                issues.append(
                    f"CI tests Python {ci_ver} but requires-python is >={min_version}"
                )

    if version_lt and ci_versions and isinstance(ci_versions, list):
        lt_tuple = parse_version_tuple(str(version_lt))
        for ci_ver in ci_versions:
            ci_tuple = parse_version_tuple(ci_ver)
            if ci_tuple >= lt_tuple:
                issues.append(
                    f"CI tests Python {ci_ver} but requires-python is <{version_lt}"
                )

    # Check consistency: classifiers within range
    if min_version and classifier_versions and isinstance(classifier_versions, list):
        min_tuple = parse_version_tuple(str(min_version))
        for cls_ver in classifier_versions:
            cls_tuple = parse_version_tuple(cls_ver)
            if cls_tuple < min_tuple:
                issues.append(
                    f"Classifier lists Python {cls_ver} but requires-python is >={min_version}"
                )

    # Check consistency: imports don't exceed requires-python
    if import_min and min_version:
        import_tuple = parse_version_tuple(str(import_min))
        min_tuple = parse_version_tuple(str(min_version))
        if import_tuple > min_tuple:
            issues.append(
                f"Imports require Python {import_min}+ but requires-python is >={min_version}"
            )

    # Record consistency issues as a fact
    if issues:
        result.facts.append(
            Fact(
                key="python.consistency-issues",
                value=issues,
                source="derived",
            )
        )
