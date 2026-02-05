"""Spec data types."""

from __future__ import annotations

import hashlib
import time
import tomllib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Self


def generate_id(prefix: str) -> str:
    """Generate a unique ID with the given prefix."""
    # Use timestamp + random bytes for uniqueness
    data = f"{time.time_ns()}".encode()
    hash_bytes = hashlib.sha256(data).hexdigest()[:7]
    return f"{prefix}-{hash_bytes}"


@dataclass
class Modification:
    """A modification to a claim within a context."""

    action: str  # relax | promote | exempt
    claim: str = ""  # specific claim ID
    level: str = ""  # target all claims at this level
    topic: str = ""  # target all claims with this tag

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a modification from TOML data."""
        return cls(
            action=data.get("action", ""),
            claim=data.get("claim", ""),
            level=data.get("level", ""),
            topic=data.get("topic", ""),
        )


@dataclass
class Claim:
    """A statement that can be verified."""

    id: str
    text: str
    status: str = "pending"  # pending | confirmed | rejected | superseded
    source: str = "human"  # human | inferred | scan
    author: str = ""
    level: str = "warn"  # block | warn | skip
    tags: list[str] = field(default_factory=list)
    verify: list[str] = field(
        default_factory=list
    )  # auto | static | llm | scan | coverage
    files: list[str] = field(default_factory=list)  # for LLM verification
    evidence: list[str] = field(default_factory=list)  # for audit trail
    created: datetime | None = None
    updated: datetime | None = None

    # Optional
    why: str = ""
    considered: list[str] = field(default_factory=list)
    traces_to: list[str] = field(default_factory=list)
    supersedes: str = ""
    closes: list[str] = field(default_factory=list)

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a claim from TOML data."""
        return cls(
            id=data.get("id", ""),
            text=data.get("text", ""),
            status=data.get("status", "pending"),
            source=data.get("source", "human"),
            author=data.get("author", ""),
            level=data.get("level", "warn"),
            tags=data.get("tags", []),
            verify=data.get("verify", []),
            files=data.get("files", []),
            evidence=data.get("evidence", []),
            created=data.get("created"),
            updated=data.get("updated"),
            why=data.get("why", ""),
            considered=data.get("considered", []),
            traces_to=data.get("traces_to", []),
            supersedes=data.get("supersedes", ""),
            closes=data.get("closes", []),
        )


@dataclass
class Issue:
    """An open issue or question."""

    id: str
    text: str
    status: str = "open"  # open | closed
    tags: list[str] = field(default_factory=list)
    created: datetime | None = None
    updated: datetime | None = None
    closed_reason: str = ""  # when status = closed

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse an issue from TOML data."""
        return cls(
            id=data.get("id", ""),
            text=data.get("text", ""),
            status=data.get("status", "open"),
            tags=data.get("tags", []),
            created=data.get("created"),
            updated=data.get("updated"),
            closed_reason=data.get("closed_reason", ""),
        )


@dataclass
class Context:
    """Where different rules apply (exemptions, overrides)."""

    id: str
    name: str
    description: str = ""
    created: datetime | None = None
    updated: datetime | None = None
    expires: datetime | None = None
    modifications: list[Modification] = field(default_factory=list)

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a context from TOML data."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            created=data.get("created"),
            updated=data.get("updated"),
            expires=data.get("expires"),
            modifications=[
                Modification.parse(m) for m in data.get("modifications", [])
            ],
        )


@dataclass
class Spec:
    """A specification for a project."""

    name: str
    version: int = 1  # schema version
    created: datetime | None = None
    author: str = ""
    claims: list[Claim] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    contexts: list[Context] = field(default_factory=list)

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a spec from TOML data."""
        meta = data.get("spec", {})
        return cls(
            name=meta.get("name", ""),
            version=meta.get("version", 1),
            created=meta.get("created"),
            author=meta.get("author", ""),
            claims=[Claim.parse(c) for c in data.get("claims", [])],
            issues=[Issue.parse(i) for i in data.get("issues", [])],
            contexts=[Context.parse(c) for c in data.get("contexts", [])],
        )

    @classmethod
    def load(cls, path: Path) -> Self:
        """Load a spec from a TOML file."""
        with path.open("rb") as f:
            data = tomllib.load(f)
        return cls.parse(data)

    def get_claim(self, claim_id: str) -> Claim | None:
        """Get a claim by ID."""
        for claim in self.claims:
            if claim.id == claim_id:
                return claim
        return None

    def get_issue(self, issue_id: str) -> Issue | None:
        """Get an issue by ID."""
        for issue in self.issues:
            if issue.id == issue_id:
                return issue
        return None

    def get_context(self, context_id: str) -> Context | None:
        """Get a context by ID."""
        for context in self.contexts:
            if context.id == context_id:
                return context
        return None
