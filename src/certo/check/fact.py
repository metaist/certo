"""Fact check - config, runner, and evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Self

from certo.check.core import Check, CheckContext, CheckResult, Evidence, generate_id


@dataclass
class FactCheck(Check):
    """A check that verifies facts discovered by scan."""

    kind: str = "fact"
    id: str = ""
    status: str = "enabled"
    has: str = ""  # Fact key that must exist and be truthy
    empty: str = ""  # Fact key that must be empty/falsy
    equals: str = ""  # Fact key that must equal a specific value
    value: str = ""  # Value to compare against (for equals)
    matches: str = ""  # Fact key whose value must match regex
    pattern: str = ""  # Regex pattern (for matches)

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a fact check from TOML data."""
        check = cls(
            kind="fact",
            id=data.get("id", ""),
            status=data.get("status", "enabled"),
            has=data.get("has", ""),
            empty=data.get("empty", ""),
            equals=data.get("equals", ""),
            value=data.get("value", ""),
            matches=data.get("matches", ""),
            pattern=data.get("pattern", ""),
        )
        if not check.id:
            content = f"fact:{check.has}{check.empty}{check.equals}{check.matches}"
            check.id = generate_id("k", content)
        return check

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[checks]]",
            f'id = "{self.id}"',
            'kind = "fact"',
        ]
        if self.status != "enabled":
            lines.append(f'status = "{self.status}"')
        if self.has:
            lines.append(f'has = "{self.has}"')
        if self.empty:
            lines.append(f'empty = "{self.empty}"')
        if self.equals:
            lines.append(f'equals = "{self.equals}"')
            lines.append(f'value = "{self.value}"')
        if self.matches:
            lines.append(f'matches = "{self.matches}"')
            lines.append(f'pattern = "{self.pattern}"')
        return "\n".join(lines)


@lru_cache(maxsize=8)
def _cached_scan(root: str) -> Any:
    """Cache scan results per project root."""
    from certo.scan import scan_project

    return scan_project(Path(root))


def clear_scan_cache() -> None:
    """Clear the scan cache (for testing)."""
    _cached_scan.cache_clear()


class FactRunner:
    """Runner for fact-based checks."""

    def run(self, ctx: CheckContext, claim: Any, check: Any) -> CheckResult:
        """Verify facts discovered by scan."""
        has = getattr(check, "has", "")
        empty = getattr(check, "empty", "")
        equals = getattr(check, "equals", "")
        value = getattr(check, "value", "")
        matches = getattr(check, "matches", "")
        pattern = getattr(check, "pattern", "")

        if not has and not empty and not equals and not matches:
            return CheckResult(
                claim_id=claim.id if claim else "",
                claim_text=claim.text if claim else "",
                passed=False,
                message="Fact check has no criteria (has, empty, equals, or matches)",
                kind="fact",
            )

        scan_result = _cached_scan(str(ctx.project_root))

        # Check 'empty' - fact must be empty/falsy (or not exist)
        if empty:
            fact = scan_result.get(empty)
            if fact is not None and fact.value:
                return CheckResult(
                    claim_id=claim.id if claim else "",
                    claim_text=claim.text if claim else "",
                    passed=False,
                    message=f"Fact is not empty: {empty}={fact.value!r}",
                    kind="fact",
                )

        # Check 'has' - fact must exist and be truthy
        if has:
            fact = scan_result.get(has)
            if fact is None:
                return CheckResult(
                    claim_id=claim.id if claim else "",
                    claim_text=claim.text if claim else "",
                    passed=False,
                    message=f"Fact not found: {has}",
                    kind="fact",
                )
            if not fact.value:
                return CheckResult(
                    claim_id=claim.id if claim else "",
                    claim_text=claim.text if claim else "",
                    passed=False,
                    message=f"Fact is falsy: {has}={fact.value!r}",
                    kind="fact",
                )

        # Check 'equals' - fact must equal specific value
        if equals:
            fact = scan_result.get(equals)
            if fact is None:
                return CheckResult(
                    claim_id=claim.id if claim else "",
                    claim_text=claim.text if claim else "",
                    passed=False,
                    message=f"Fact not found: {equals}",
                    kind="fact",
                )
            if str(fact.value) != value:
                return CheckResult(
                    claim_id=claim.id if claim else "",
                    claim_text=claim.text if claim else "",
                    passed=False,
                    message=f"Fact mismatch: {equals}={fact.value!r}, expected {value!r}",
                    kind="fact",
                )

        # Check 'matches' - fact must match regex pattern
        if matches:
            fact = scan_result.get(matches)
            if fact is None:
                return CheckResult(
                    claim_id=claim.id if claim else "",
                    claim_text=claim.text if claim else "",
                    passed=False,
                    message=f"Fact not found: {matches}",
                    kind="fact",
                )
            if not re.search(pattern, str(fact.value)):
                return CheckResult(
                    claim_id=claim.id if claim else "",
                    claim_text=claim.text if claim else "",
                    passed=False,
                    message=f"Fact doesn't match: {matches}={fact.value!r}, pattern={pattern!r}",
                    kind="fact",
                )

        return CheckResult(
            claim_id=claim.id if claim else "",
            claim_text=claim.text if claim else "",
            passed=True,
            message="Fact check passed",
            kind="fact",
        )


@dataclass
class FactEvidence(Evidence):
    """Evidence from a fact/scan check."""

    kind: str = "fact"
    facts: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = super().to_dict()
        d["facts"] = self.facts
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        timestamp = data.get("timestamp", "")
        return cls(
            check_id=data["check_id"],
            kind=data.get("kind", "fact"),
            timestamp=datetime.fromisoformat(timestamp) if timestamp else None,
            duration=data.get("duration", 0.0),
            check_hash=data.get("check_hash", ""),
            facts=data.get("facts", {}),
        )
