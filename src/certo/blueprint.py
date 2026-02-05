"""Blueprint data types."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Self


@dataclass
class Decision:
    """An explicit choice made during specification."""

    id: str
    title: str
    status: str = "proposed"  # proposed | confirmed | superseded | deferred
    description: str = ""
    alternatives: list[str] = field(default_factory=list)
    rationale: str = ""
    decided_by: str = ""
    decided_on: datetime | None = None

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a decision from TOML data."""
        return cls(
            id=data.get("id", "unknown"),
            title=data.get("title", ""),
            status=data.get("status", "proposed"),
            description=data.get("description", ""),
            alternatives=data.get("alternatives", []),
            rationale=data.get("rationale", ""),
            decided_by=data.get("decided_by", ""),
            decided_on=data.get("decided_on"),
        )


@dataclass
class Concern:
    """A statement that must be true, with verification strategy."""

    id: str
    claim: str
    category: str = ""
    strategy: str = "auto"  # auto | static | llm | test
    context: list[str] = field(default_factory=list)
    verify_with: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    failure: str = "warn"  # warn | block-commit | block-release
    traces_to: list[str] = field(default_factory=list)

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a concern from TOML data."""
        return cls(
            id=data.get("id", "unknown"),
            claim=data.get("claim", ""),
            category=data.get("category", ""),
            strategy=data.get("strategy", "auto"),
            context=data.get("context", []),
            verify_with=data.get("verify_with", []),
            conditions=data.get("conditions", []),
            failure=data.get("failure", "warn"),
            traces_to=data.get("traces_to", []),
        )


@dataclass
class Context:
    """Where different rules apply (exemptions, overrides)."""

    id: str
    name: str
    description: str = ""
    applies_to: list[str] = field(default_factory=list)
    expires: datetime | None = None
    overrides: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a context from TOML data."""
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            applies_to=data.get("applies_to", []),
            expires=data.get("expires"),
            overrides=data.get("overrides", {}),
        )


@dataclass
class Blueprint:
    """A living specification for a project."""

    name: str
    version: str = ""
    created: datetime | None = None
    author: str = ""
    description: str = ""
    decisions: list[Decision] = field(default_factory=list)
    concerns: list[Concern] = field(default_factory=list)
    contexts: list[Context] = field(default_factory=list)

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a blueprint from TOML data."""
        meta = data.get("blueprint", {})
        return cls(
            name=meta.get("name", ""),
            version=meta.get("version", ""),
            created=meta.get("created"),
            author=meta.get("author", ""),
            description=meta.get("description", ""),
            decisions=[Decision.parse(d) for d in data.get("decisions", [])],
            concerns=[Concern.parse(c) for c in data.get("concerns", [])],
            contexts=[Context.parse(c) for c in data.get("contexts", [])],
        )

    @classmethod
    def load(cls, path: Path) -> Self:
        """Load a blueprint from a TOML file."""
        with path.open("rb") as f:
            data = tomllib.load(f)
        return cls.parse(data)

    def get_concern(self, concern_id: str) -> Concern | None:
        """Get a concern by ID."""
        for concern in self.concerns:
            if concern.id == concern_id:
                return concern
        return None

    def get_decision(self, decision_id: str) -> Decision | None:
        """Get a decision by ID."""
        for decision in self.decisions:
            if decision.id == decision_id:
                return decision
        return None
