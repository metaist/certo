"""Python stdlib version knowledge."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources


@dataclass
class ModuleVersionInfo:
    """Version information for a stdlib module."""

    name: str
    added: str  # e.g., "3.11"
    removed: str | None = None  # e.g., "3.12" or None if still present


def parse_versions_file(content: str) -> dict[str, ModuleVersionInfo]:
    """Parse typeshed VERSIONS file format.

    Format: module: X.Y- or module: X.Y-A.B
    """
    modules: dict[str, ModuleVersionInfo] = {}

    for line in content.splitlines():
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # Parse "module: X.Y-" or "module: X.Y-A.B"
        if ":" not in line:
            continue

        name, version_range = line.split(":", 1)
        name = name.strip()
        version_range = version_range.strip()

        # Parse version range
        if "-" in version_range:
            parts = version_range.split("-")
            added = parts[0]
            removed = parts[1] if parts[1] else None
        else:
            added = version_range
            removed = None

        modules[name] = ModuleVersionInfo(name=name, added=added, removed=removed)

    return modules


def load_stdlib_versions() -> dict[str, ModuleVersionInfo]:
    """Load stdlib version info from bundled typeshed data."""
    # Use importlib.resources to load package data
    kb_path = resources.files("certo.kb.python.typeshed")
    versions_file = kb_path.joinpath("VERSIONS")
    content = versions_file.read_text()
    return parse_versions_file(content)


def get_min_python_version(module_name: str) -> str | None:
    """Get the minimum Python version that includes a module.

    Returns None if module is not in stdlib.
    """
    versions = load_stdlib_versions()
    if module_name in versions:
        return versions[module_name].added
    return None


def is_module_removed(module_name: str, python_version: str) -> bool:
    """Check if a module is not available in a Python version.

    Typeshed VERSIONS format uses "last version available", e.g.:
    distutils: 3.0-3.11 means distutils exists in 3.11 but not in 3.12+

    Returns True if the module is NOT available in python_version.
    """
    versions = load_stdlib_versions()
    if module_name not in versions:
        return False

    removed = versions[module_name].removed
    if removed is None:
        return False

    # "removed" is the last version where the module exists
    # So the module is gone if python_version > removed
    removed_tuple = tuple(int(x) for x in removed.split("."))
    check_tuple = tuple(int(x) for x in python_version.split("."))

    return check_tuple > removed_tuple
