"""Spec data types."""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Self

from certo.probe.core import ProbeConfig
from certo.probe.verify import Verify


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
            "[[certo.claims]]",
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
            lines.append("")
            lines.append("[certo.claims.verify]")
            for key, conditions in self.verify.rules.items():
                lines.append(f'"{key}" = {conditions}')
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
class Spec:
    """A certo specification for a project."""

    name: str = ""
    version: int = 1  # schema version
    created: datetime | None = None
    author: str = ""
    imports: list[str] = field(default_factory=list)
    checks: list[ProbeConfig] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a spec from TOML data.

        Supports both new [certo] format and legacy [spec] format.
        """
        from certo.probe import parse_probe

        # Try new [certo] format first, fall back to legacy [spec]
        certo = data.get("certo", {})
        if not certo:
            # Legacy format: [spec] + top-level [[probes]]/[[claims]]
            meta = data.get("spec", {})
            probes_data = data.get("probes", []) or data.get("checks", [])
            claims_data = data.get("claims", [])
        else:
            # New format: everything under [certo]
            meta = certo
            probes_data = certo.get("probes", [])
            claims_data = certo.get("claims", [])

        return cls(
            name=meta.get("name", ""),
            version=meta.get("version", 1),
            created=meta.get("created"),
            author=meta.get("author", ""),
            imports=meta.get("imports", []),
            checks=[parse_probe(c) for c in probes_data],
            claims=[Claim.parse(c) for c in claims_data],
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

    def get_check(self, check_id: str) -> ProbeConfig | None:
        """Get a check by ID."""
        for check in self.checks:
            if check.id == check_id:
                return check
        return None

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "# Certo Spec",
            "# https://github.com/metaist/certo",
            "",
            "[certo]",
            f"version = {self.version}",
        ]
        if self.name:
            lines.append(f'name = "{self.name}"')
        if self.created:
            lines.append(f"created = {format_datetime(self.created)}")
        if self.author:
            lines.append(f'author = "{self.author}"')
        if self.imports:
            lines.append(f"imports = {self.imports}")

        if self.checks:
            lines.append("")
            lines.append("# " + "=" * 77)
            lines.append("# PROBES")
            lines.append("# " + "=" * 77)
            for check in self.checks:
                lines.append("")
                lines.append(check.to_toml())

        if self.claims:
            lines.append("")
            lines.append("# " + "=" * 77)
            lines.append("# CLAIMS")
            lines.append("# " + "=" * 77)
            for claim in self.claims:
                lines.append("")
                lines.append(claim.to_toml())

        lines.append("")
        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Save the spec to a TOML file."""
        path.write_text(self.to_toml())
