"""Spec data types."""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Self


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

    def to_toml_inline(self) -> str:
        """Serialize to inline TOML."""
        parts = [f'action = "{self.action}"']
        if self.claim:
            parts.append(f'claim = "{self.claim}"')
        if self.level:
            parts.append(f'level = "{self.level}"')
        if self.topic:
            parts.append(f'topic = "{self.topic}"')
        return "{ " + ", ".join(parts) + " }"


@dataclass
class ShellCheck:
    """A check that runs a shell command."""

    kind: Literal["shell"] = "shell"
    cmd: str = ""
    exit_code: int = 0
    matches: list[str] = field(default_factory=list)
    not_matches: list[str] = field(default_factory=list)
    timeout: int = 60

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a shell check from TOML data."""
        return cls(
            kind="shell",
            cmd=data.get("cmd", ""),
            exit_code=data.get("exit_code", 0),
            matches=data.get("matches", []),
            not_matches=data.get("not_matches", []),
            timeout=data.get("timeout", 60),
        )

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[claims.checks]]",
            'kind = "shell"',
            f'cmd = "{self.cmd}"',
        ]
        if self.exit_code != 0:
            lines.append(f"exit_code = {self.exit_code}")
        if self.matches:
            lines.append(f"matches = {self.matches}")
        if self.not_matches:
            lines.append(f"not_matches = {self.not_matches}")
        if self.timeout != 60:
            lines.append(f"timeout = {self.timeout}")
        return "\n".join(lines)


@dataclass
class LLMCheck:
    """A check that uses LLM verification."""

    kind: Literal["llm"] = "llm"
    files: list[str] = field(default_factory=list)
    prompt: str | None = None

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse an LLM check from TOML data."""
        return cls(
            kind="llm",
            files=data.get("files", []),
            prompt=data.get("prompt"),
        )

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[claims.checks]]",
            'kind = "llm"',
        ]
        if self.files:
            lines.append(f"files = {self.files}")
        if self.prompt:
            lines.append(f'prompt = "{self.prompt}"')
        return "\n".join(lines)


Check = ShellCheck | LLMCheck


def parse_check(data: dict[str, Any]) -> Check:
    """Parse a check from TOML data, dispatching on kind."""
    kind = data.get("kind", "")
    if kind == "shell":
        return ShellCheck.parse(data)
    elif kind == "llm":
        return LLMCheck.parse(data)
    else:
        raise ValueError(f"Unknown check kind: {kind}")


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
    checks: list[Check] = field(default_factory=list)
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
            checks=[parse_check(c) for c in data.get("checks", [])],
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
        # Add checks as nested tables
        for check in self.checks:
            lines.append("")
            lines.append(check.to_toml())
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

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[contexts]]",
            f'id = "{self.id}"',
            f'name = "{self.name}"',
        ]
        if self.description:
            lines.append(f'description = "{self.description}"')
        if self.created:
            lines.append(f"created = {format_datetime(self.created)}")
        if self.updated:
            lines.append(f"updated = {format_datetime(self.updated)}")
        if self.expires:
            lines.append(f"expires = {format_datetime(self.expires)}")
        if self.modifications:
            mods = ", ".join(m.to_toml_inline() for m in self.modifications)
            lines.append(f"modifications = [{mods}]")
        return "\n".join(lines)


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

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "# Certo Spec",
            "# WARNING: This file is managed by certo. Manual edits may be overwritten.",
            "# Use `certo claim`, `certo issue`, `certo context` to make changes.",
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

        if self.contexts:
            lines.append("# " + "=" * 77)
            lines.append("# CONTEXTS")
            lines.append("# " + "=" * 77)
            lines.append("")
            for context in self.contexts:
                lines.append(context.to_toml())
                lines.append("")

        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Save the spec to a TOML file."""
        path.write_text(self.to_toml())
