"""Evidence types - re-exports from check modules for convenience."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Self

# Re-export evidence types from their source modules
from certo.check.fact import FactEvidence
from certo.check.llm import LlmEvidence
from certo.check.shell import ShellEvidence
from certo.check.url import UrlEvidence


@dataclass
class Evidence:
    """Base evidence type for type hints and loading."""

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


# Type alias for any evidence type (defined after Evidence class)
AnyEvidence = Evidence | ShellEvidence | UrlEvidence | LlmEvidence | FactEvidence

__all__ = [
    "AnyEvidence",
    "Evidence",
    "ShellEvidence",
    "UrlEvidence",
    "LlmEvidence",
    "FactEvidence",
    "load_evidence",
    "save_evidence",
]


def load_evidence(path: Path) -> AnyEvidence:
    """Load evidence from JSON file, returning appropriate type."""
    data = json.loads(path.read_text())
    kind = data.get("kind", "")
    match kind:
        case "shell":
            return ShellEvidence.from_dict(data)
        case "url":
            return UrlEvidence.from_dict(data)
        case "llm":
            return LlmEvidence.from_dict(data)
        case "fact":
            return FactEvidence.from_dict(data)
        case _:
            return Evidence.from_dict(data)


def save_evidence(evidence: AnyEvidence, path: Path) -> None:
    """Save evidence to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence.to_dict(), indent=2))
