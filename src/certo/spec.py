"""Spec data types."""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Self

from certo.check.core import Check
from certo.check.verify import Verify


def generate_id(prefix: str, text: str) -> str:
    """Generate a unique ID with the given prefix based on text content."""
    hash_bytes = hashlib.sha256(text.encode()).hexdigest()[:7]
    return f"{prefix}-{hash_bytes}"


def now_utc() -> datetime:
    """Get current time in UTC."""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime | None) -> str:
    """Format datetime for TOML output."""
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


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
    verify: Verify | None = None  # Verify conditions on evidence
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
        verify_data = data.get("verify")
        verify = Verify.parse(verify_data) if verify_data else None

        return cls(
            id=data.get("id", ""),
            text=data.get("text", ""),
            status=data.get("status", "pending"),
            source=data.get("source", "human"),
            author=data.get("author", ""),
            level=data.get("level", "warn"),
            tags=data.get("tags", []),
            verify=verify,
            evidence=data.get("evidence", []),
            created=data.get("created"),
            updated=data.get("updated"),
            why=data.get("why", ""),
            considered=data.get("considered", []),
            traces_to=data.get("traces_to", []),
            supersedes=data.get("supersedes", ""),
            closes=data.get("closes", []),
        )

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[claims]]",
            f'id = "{self.id}"',
            f'text = "{self.text}"',
            f'status = "{self.status}"',
            f'source = "{self.source}"',
        ]
        if self.author:
            lines.append(f'author = "{self.author}"')
        lines.append(f'level = "{self.level}"')
        if self.tags:
            lines.append(f"tags = {self.tags}")
        if self.verify:
            lines.append(f"verify = {self.verify.to_dict()}")
        if self.created:
            lines.append(f"created = {format_datetime(self.created)}")
        if self.updated:
            lines.append(f"updated = {format_datetime(self.updated)}")
        if self.why:
            lines.append(f'why = "{self.why}"')
        if self.considered:
            lines.append(f"considered = {self.considered}")
        if self.traces_to:
            lines.append(f"traces_to = {self.traces_to}")
        if self.supersedes:
            lines.append(f'supersedes = "{self.supersedes}"')
        if self.closes:
            lines.append(f"closes = {self.closes}")
        return "\n".join(lines)


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

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[issues]]",
            f'id = "{self.id}"',
            f'text = "{self.text}"',
            f'status = "{self.status}"',
        ]
        if self.tags:
            lines.append(f"tags = {self.tags}")
        if self.created:
            lines.append(f"created = {format_datetime(self.created)}")
        if self.updated:
            lines.append(f"updated = {format_datetime(self.updated)}")
        if self.closed_reason:
            lines.append(f'closed_reason = "{self.closed_reason}"')
        return "\n".join(lines)


@dataclass
class Spec:
    """A specification for a project."""

    name: str
    version: int = 1  # schema version
    created: datetime | None = None
    author: str = ""
    checks: list[Check] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a spec from TOML data."""
        from certo.check import parse_check

        meta = data.get("spec", {})
        return cls(
            name=meta.get("name", ""),
            version=meta.get("version", 1),
            created=meta.get("created"),
            author=meta.get("author", ""),
            checks=[parse_check(c) for c in data.get("checks", [])],
            claims=[Claim.parse(c) for c in data.get("claims", [])],
            issues=[Issue.parse(i) for i in data.get("issues", [])],
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

    def get_check(self, check_id: str) -> Check | None:
        """Get a check by ID."""
        for check in self.checks:
            if check.id == check_id:
                return check
        return None

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "# Certo Spec",
            "# WARNING: This file is managed by certo. Manual edits may be overwritten.",
            "# Use `certo claim`, `certo issue`, `certo check` to make changes.",
            "",
            "[spec]",
            f'name = "{self.name}"',
            f"version = {self.version}",
        ]
        if self.created:
            lines.append(f"created = {format_datetime(self.created)}")
        if self.author:
            lines.append(f'author = "{self.author}"')
        lines.append("")

        if self.checks:
            lines.append("# " + "=" * 77)
            lines.append("# CHECKS")
            lines.append("# " + "=" * 77)
            lines.append("")
            for check in self.checks:
                lines.append(check.to_toml())
                lines.append("")

        if self.claims:
            lines.append("# " + "=" * 77)
            lines.append("# CLAIMS")
            lines.append("# " + "=" * 77)
            lines.append("")
            for claim in self.claims:
                lines.append(claim.to_toml())
                lines.append("")

        if self.issues:
            lines.append("# " + "=" * 77)
            lines.append("# ISSUES")
            lines.append("# " + "=" * 77)
            lines.append("")
            for issue in self.issues:
                lines.append(issue.to_toml())
                lines.append("")

        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Save the spec to a TOML file."""
        path.write_text(self.to_toml())
