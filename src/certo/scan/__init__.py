"""Project scanning and fact discovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Fact:
    """A discovered fact about the project."""

    key: str  # e.g., "python.min-version", "uses.uv", "file.exists.Cargo.toml"
    value: str | bool | list[str]  # The fact value
    source: str  # e.g., "pyproject.toml:5"
    confidence: float = 1.0  # 0.0-1.0, how certain we are


@dataclass
class ScanResult:
    """Result of scanning a project."""

    facts: list[Fact] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)  # Scan errors (not project issues)

    def get(self, key: str) -> Fact | None:
        """Get a fact by key."""
        for fact in self.facts:
            if fact.key == key:
                return fact
        return None

    def has(self, key: str) -> bool:
        """Check if a fact exists and is truthy."""
        fact = self.get(key)
        if fact is None:
            return False
        if isinstance(fact.value, bool):
            return fact.value
        if isinstance(fact.value, str):
            return bool(fact.value)
        if isinstance(fact.value, list):
            return len(fact.value) > 0
        return True

    def get_value(
        self, key: str, default: str | bool | list[str] | None = None
    ) -> str | bool | list[str] | None:
        """Get a fact's value by key."""
        fact = self.get(key)
        return fact.value if fact else default

    def filter(self, prefix: str) -> list[Fact]:
        """Get all facts with keys starting with prefix."""
        return [f for f in self.facts if f.key.startswith(prefix)]


def scan_project(root: Path) -> ScanResult:
    """Scan a project and return discovered facts."""
    from certo.scan.python import scan_python

    result = ScanResult()

    # Run all scanners
    scan_python(root, result)

    return result


# Re-export for convenience
__all__ = ["Fact", "ScanResult", "scan_project"]
