"""Core probe types - shared by all probes."""

from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, Self

if TYPE_CHECKING:
    from certo.spec import Claim as Rule, Spec


def generate_id(prefix: str, content: str) -> str:
    """Generate a short hash-based ID."""
    h = hashlib.sha256(content.encode()).hexdigest()[:7]
    return f"{prefix}-{h}"


@dataclass
class Fact:
    """Base class for facts produced by probes."""

    probe_id: str
    kind: str
    timestamp: datetime | None = None
    duration: float = 0.0
    probe_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "probe_id": self.probe_id,
            "kind": self.kind,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
            "duration": self.duration,
            "probe_hash": self.probe_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        timestamp = data.get("timestamp", "")
        return cls(
            probe_id=data["probe_id"],
            kind=data["kind"],
            timestamp=datetime.fromisoformat(timestamp) if timestamp else None,
            duration=data.get("duration", 0.0),
            probe_hash=data.get("probe_hash", ""),
        )

    def save(self, path: Path) -> None:
        """Save fact to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> Self:
        """Load fact from JSON file."""
        data = json.loads(path.read_text())
        return cls.from_dict(data)


@dataclass
class ProbeResult:
    """Result of a single probe execution."""

    rule_id: str
    rule_text: str
    passed: bool
    message: str
    kind: str  # Probe kind: shell, llm, scan, url, none
    probe_id: str = ""  # ID of the specific probe (if applicable)
    output: str = ""  # Full command output (for shell probes)
    skipped: bool = False  # Was this probe skipped?
    skip_reason: str = ""  # Why was it skipped?

    def to_fact(self) -> "ResultFact":
        """Convert to Fact for verification."""
        return ResultFact(
            probe_id=self.probe_id,
            kind=self.kind,
            passed=self.passed,
            message=self.message,
            output=self.output,
            skipped=self.skipped,
            skip_reason=self.skip_reason,
        )


@dataclass
class ResultFact(Fact):
    """Fact created from a ProbeResult for verification."""

    kind: str = "result"
    passed: bool = False
    message: str = ""
    output: str = ""
    skipped: bool = False
    skip_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for selector traversal."""
        d = super().to_dict()
        d["passed"] = self.passed
        d["message"] = self.message
        d["output"] = self.output
        d["skipped"] = self.skipped
        d["skip_reason"] = self.skip_reason
        return d


@dataclass
class ProbeContext:
    """Context for running probes."""

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
class ProbeConfig:
    """Base class for all probe configurations."""

    kind: str = ""
    id: str = ""
    status: str = "enabled"  # "enabled" | "disabled"
    cache_key: list[str] | None = None  # File globs for cache invalidation

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse from TOML data. Override in subclasses."""
        raise NotImplementedError

    def to_toml(self) -> str:
        """Serialize to TOML. Override in subclasses."""
        raise NotImplementedError

    def content_hash(self) -> str:
        """Generate hash of probe definition for cache invalidation."""
        # Subclasses should override to include their specific fields
        return generate_id("h", f"{self.kind}:{self.id}")


class Probe(Protocol):
    """Protocol for probes that gather facts."""

    def run(self, ctx: ProbeContext, rule: Rule | None, config: Any) -> ProbeResult:
        """Run the probe and return a result."""
        ...  # pragma: no cover
