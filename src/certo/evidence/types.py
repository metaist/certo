"""Evidence data types."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Self


@dataclass
class Evidence:
    """Base evidence from a check run."""

    check_id: str
    kind: str
    timestamp: datetime
    duration: float
    check_hash: str = ""  # Hash of check definition for cache invalidation

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "check_id": self.check_id,
            "kind": self.kind,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "check_hash": self.check_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            check_id=data["check_id"],
            kind=data["kind"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration=data["duration"],
            check_hash=data.get("check_hash", ""),
        )

    def save(self, path: Path) -> None:
        """Save evidence to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> Evidence:
        """Load evidence from JSON file, returning appropriate subclass."""
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
                return cls.from_dict(data)


@dataclass
class ShellEvidence(Evidence):
    """Evidence from a shell command check."""

    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    json: dict[str, Any] | list[Any] | None = None  # Parsed JSON if available

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = super().to_dict()
        d.update(
            {
                "exit_code": self.exit_code,
                "stdout": self.stdout,
                "stderr": self.stderr,
            }
        )
        if self.json is not None:
            d["json"] = self.json
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            check_id=data["check_id"],
            kind=data["kind"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration=data["duration"],
            check_hash=data.get("check_hash", ""),
            exit_code=data.get("exit_code", 0),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            json=data.get("json"),
        )


@dataclass
class UrlEvidence(Evidence):
    """Evidence from a URL check."""

    status_code: int = 0
    body: str = ""
    json: dict[str, Any] | list[Any] | None = None  # Parsed JSON if available

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = super().to_dict()
        d.update(
            {
                "status_code": self.status_code,
                "body": self.body,
            }
        )
        if self.json is not None:
            d["json"] = self.json
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            check_id=data["check_id"],
            kind=data["kind"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration=data["duration"],
            check_hash=data.get("check_hash", ""),
            status_code=data.get("status_code", 0),
            body=data.get("body", ""),
            json=data.get("json"),
        )


@dataclass
class LlmEvidence(Evidence):
    """Evidence from an LLM check."""

    verdict: bool = False
    reasoning: str = ""
    model: str = ""
    tokens: dict[str, int] = field(default_factory=dict)  # input, output

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = super().to_dict()
        d.update(
            {
                "verdict": self.verdict,
                "reasoning": self.reasoning,
                "model": self.model,
                "tokens": self.tokens,
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            check_id=data["check_id"],
            kind=data["kind"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration=data["duration"],
            check_hash=data.get("check_hash", ""),
            verdict=data.get("verdict", False),
            reasoning=data.get("reasoning", ""),
            model=data.get("model", ""),
            tokens=data.get("tokens", {}),
        )


@dataclass
class FactEvidence(Evidence):
    """Evidence from a fact/scan check."""

    facts: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = super().to_dict()
        d["facts"] = self.facts
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            check_id=data["check_id"],
            kind=data["kind"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration=data["duration"],
            check_hash=data.get("check_hash", ""),
            facts=data.get("facts", {}),
        )
