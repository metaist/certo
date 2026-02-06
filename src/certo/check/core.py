"""Core check types - shared by all runners."""

from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, Self

if TYPE_CHECKING:
    from certo.spec import Claim, Spec


def generate_id(prefix: str, content: str) -> str:
    """Generate a short hash-based ID."""
    h = hashlib.sha256(content.encode()).hexdigest()[:7]
    return f"{prefix}-{h}"


@dataclass
class Evidence:
    """Base class for evidence produced by checks."""

    check_id: str
    kind: str
    timestamp: datetime | None = None
    duration: float = 0.0
    check_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "check_id": self.check_id,
            "kind": self.kind,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
            "duration": self.duration,
            "check_hash": self.check_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        timestamp = data.get("timestamp", "")
        return cls(
            check_id=data["check_id"],
            kind=data["kind"],
            timestamp=datetime.fromisoformat(timestamp) if timestamp else None,
            duration=data.get("duration", 0.0),
            check_hash=data.get("check_hash", ""),
        )

    def save(self, path: Path) -> None:
        """Save evidence to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> Self:
        """Load evidence from JSON file."""
        data = json.loads(path.read_text())
        return cls.from_dict(data)


@dataclass
class CheckResult:
    """Result of a single verification check."""

    claim_id: str
    claim_text: str
    passed: bool
    message: str
    kind: str  # Check kind: shell, llm, fact, url, none
    check_id: str = ""  # ID of the specific check (if applicable)
    output: str = ""  # Full command output (for shell checks)
    skipped: bool = False  # Was this check skipped?
    skip_reason: str = ""  # Why was it skipped?


@dataclass
class CheckContext:
    """Context for running checks."""

    project_root: Path
    spec_path: Path
    spec: Spec | None = None
    offline: bool = False
    no_cache: bool = False
    model: str | None = None

    @property
    def root(self) -> Path:
        """Alias for project_root."""
        return self.project_root


@dataclass
class Check:
    """Base class for all check configurations."""

    kind: str = ""
    id: str = ""
    status: str = "enabled"  # "enabled" | "disabled"

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse from TOML data. Override in subclasses."""
        raise NotImplementedError

    def to_toml(self) -> str:
        """Serialize to TOML. Override in subclasses."""
        raise NotImplementedError


class Runner(Protocol):
    """Protocol for check runners."""

    def run(self, ctx: CheckContext, claim: Claim, check: Any) -> CheckResult:
        """Run the check and return a result."""
        ...  # pragma: no cover
