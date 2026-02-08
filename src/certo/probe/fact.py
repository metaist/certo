"""Scan probe - config, probe, and fact. Checks facts from certo scan."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Self

from certo.probe.core import Fact, ProbeConfig, ProbeContext, ProbeResult, generate_id


@dataclass
class ScanConfig(ProbeConfig):
    """Configuration for a scan-based probe."""

    kind: str = "scan"
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
        """Parse a scan probe config from TOML data."""
        config = cls(
            kind="scan",
            id=data.get("id", ""),
            status=data.get("status", "enabled"),
            has=data.get("has", ""),
            empty=data.get("empty", ""),
            equals=data.get("equals", ""),
            value=data.get("value", ""),
            matches=data.get("matches", ""),
            pattern=data.get("pattern", ""),
        )
        if not config.id:
            content = f"scan:{config.has}{config.empty}{config.equals}{config.matches}"
            config.id = generate_id("k", content)
        return config

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[certo.probes]]",
            f'id = "{self.id}"',
            'kind = "scan"',
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


class ScanProbe:
    """Probe that checks facts discovered by scan."""

    def run(self, ctx: ProbeContext, rule: Any, config: Any) -> ProbeResult:
        """Verify facts discovered by scan."""
        has = getattr(config, "has", "")
        empty = getattr(config, "empty", "")
        equals = getattr(config, "equals", "")
        value = getattr(config, "value", "")
        matches = getattr(config, "matches", "")
        pattern = getattr(config, "pattern", "")

        if not has and not empty and not equals and not matches:
            return ProbeResult(
                rule_id=rule.id if rule else "",
                rule_text=rule.text if rule else "",
                passed=False,
                message="Scan probe has no criteria (has, empty, equals, or matches)",
                kind="scan",
            )

        scan_result = _cached_scan(str(ctx.project_root))

        # Check 'empty' - fact must be empty/falsy (or not exist)
        if empty:
            fact = scan_result.get(empty)
            if fact is not None and fact.value:
                return ProbeResult(
                    rule_id=rule.id if rule else "",
                    rule_text=rule.text if rule else "",
                    passed=False,
                    message=f"Fact is not empty: {empty}={fact.value!r}",
                    kind="scan",
                )

        # Check 'has' - fact must exist and be truthy
        if has:
            fact = scan_result.get(has)
            if fact is None:
                return ProbeResult(
                    rule_id=rule.id if rule else "",
                    rule_text=rule.text if rule else "",
                    passed=False,
                    message=f"Fact not found: {has}",
                    kind="scan",
                )
            if not fact.value:
                return ProbeResult(
                    rule_id=rule.id if rule else "",
                    rule_text=rule.text if rule else "",
                    passed=False,
                    message=f"Fact is falsy: {has}={fact.value!r}",
                    kind="scan",
                )

        # Check 'equals' - fact must equal specific value
        if equals:
            fact = scan_result.get(equals)
            if fact is None:
                return ProbeResult(
                    rule_id=rule.id if rule else "",
                    rule_text=rule.text if rule else "",
                    passed=False,
                    message=f"Fact not found: {equals}",
                    kind="scan",
                )
            if str(fact.value) != value:
                return ProbeResult(
                    rule_id=rule.id if rule else "",
                    rule_text=rule.text if rule else "",
                    passed=False,
                    message=f"Fact mismatch: {equals}={fact.value!r}, expected {value!r}",
                    kind="scan",
                )

        # Check 'matches' - fact must match regex pattern
        if matches:
            fact = scan_result.get(matches)
            if fact is None:
                return ProbeResult(
                    rule_id=rule.id if rule else "",
                    rule_text=rule.text if rule else "",
                    passed=False,
                    message=f"Fact not found: {matches}",
                    kind="scan",
                )
            if not re.search(pattern, str(fact.value)):
                return ProbeResult(
                    rule_id=rule.id if rule else "",
                    rule_text=rule.text if rule else "",
                    passed=False,
                    message=f"Fact doesn't match: {matches}={fact.value!r}, pattern={pattern!r}",
                    kind="scan",
                )

        return ProbeResult(
            rule_id=rule.id if rule else "",
            rule_text=rule.text if rule else "",
            passed=True,
            message="Scan probe passed",
            kind="scan",
        )


@dataclass
class ScanFact(Fact):
    """Fact from a scan probe."""

    kind: str = "scan"
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
            probe_id=data["probe_id"],
            kind=data.get("kind", "scan"),
            timestamp=datetime.fromisoformat(timestamp) if timestamp else None,
            duration=data.get("duration", 0.0),
            probe_hash=data.get("probe_hash", ""),
            facts=data.get("facts", {}),
        )
