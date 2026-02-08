"""Probes that gather facts from the world.

Each probe type is self-contained in its own module with the
configuration dataclass, probe runner, and fact type.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certo.probe.core import (
    Fact,
    Probe,
    ProbeConfig,
    ProbeContext,
    ProbeResult,
    ResultFact,
    generate_id,
)
from certo.probe.fact import ScanConfig, ScanProbe, clear_scan_cache
from certo.probe.llm import LLMConfig, LLMProbe
from certo.probe.shell import ShellConfig, ShellProbe
from certo.probe.url import UrlConfig, UrlProbe
from certo.probe.verify import Verify, VerifyResult, verify_rule

# Registry mapping kind -> (ConfigClass, ProbeInstance)
REGISTRY: dict[str, tuple[type[ProbeConfig], Probe]] = {
    "shell": (ShellConfig, ShellProbe()),
    "llm": (LLMConfig, LLMProbe()),
    "scan": (ScanConfig, ScanProbe()),
    "url": (UrlConfig, UrlProbe()),
}


def parse_probe(data: dict[str, Any]) -> ProbeConfig:
    """Parse a probe config from TOML data, dispatching on kind."""
    kind = data.get("kind", "")
    if kind not in REGISTRY:
        raise ValueError(f"Unknown probe kind: {kind}")
    config_cls, _ = REGISTRY[kind]
    return config_cls.parse(data)


def get_probe(kind: str) -> Probe | None:
    """Get the probe for a config kind."""
    entry = REGISTRY.get(kind)
    return entry[1] if entry else None


def check_spec(
    spec_path: Path,
    *,
    offline: bool = False,
    no_cache: bool = False,
    model: str | None = None,
    only: set[str] | None = None,
    skip: set[str] | None = None,
) -> list[ProbeResult]:
    """Run all spec probes and verify rules.

    Args:
        spec_path: Path to spec.toml
        offline: Skip LLM probes
        no_cache: Ignore cached results
        model: LLM model to use
        only: If set, only run probes for these rule/probe IDs
        skip: Skip probes for these rule/probe IDs
    """
    from certo.spec import Spec

    project_root = spec_path.parent.parent  # .certo/spec.toml -> project root

    ctx = ProbeContext(
        project_root=project_root,
        spec_path=spec_path,
        offline=offline,
        no_cache=no_cache,
        model=model,
    )

    results: list[ProbeResult] = []
    skip = skip or set()

    # Load spec - fail early if can't parse
    try:
        ctx.spec = Spec.load(spec_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Spec not found: {spec_path}") from None
    except Exception as e:
        raise ValueError(f"Failed to parse spec: {e}") from None

    # Run probes
    for probe_config in ctx.spec.checks:
        probe_id = probe_config.id or ""

        # Skip disabled probes
        if probe_config.status == "disabled":
            results.append(
                ProbeResult(
                    rule_id="",
                    rule_text="",
                    passed=True,
                    message="probe disabled",
                    kind="none",
                    probe_id=probe_id,
                    skipped=True,
                    skip_reason="probe disabled",
                )
            )
            continue

        # Skip this specific probe if in skip set
        if probe_id and probe_id in skip:
            results.append(
                ProbeResult(
                    rule_id="",
                    rule_text="",
                    passed=True,
                    message="--skip flag",
                    kind="none",
                    probe_id=probe_id,
                    skipped=True,
                    skip_reason="--skip flag",
                )
            )
            continue

        # If --only specified with probe IDs, only run matching probes
        if only is not None and probe_id not in only:
            continue  # Silently skip --only filtered

        # Get probe from registry
        probe = get_probe(probe_config.kind)
        if probe is None:  # pragma: no cover
            continue  # Unknown probe type

        # Run probe to collect fact
        # Note: probes still expect (ctx, rule, config) - pass None for rule
        result = probe.run(ctx, None, probe_config)
        result.probe_id = probe_id
        results.append(result)

    # Build fact map from probe results
    fact_map: dict[str, Fact] = {}
    for result in results:
        if result.probe_id and not result.skipped:
            fact_map[result.probe_id] = result.to_fact()

    # Verify rules (still called "claims" in spec for now)
    for rule in ctx.spec.claims:
        # Skip rules that shouldn't be checked
        if rule.status in ("rejected", "superseded"):
            results.append(
                ProbeResult(
                    rule_id=rule.id,
                    rule_text=rule.text,
                    passed=True,
                    message=f"status={rule.status}",
                    kind="none",
                    skipped=True,
                    skip_reason=f"status={rule.status}",
                )
            )
            continue

        if rule.level == "skip":
            results.append(
                ProbeResult(
                    rule_id=rule.id,
                    rule_text=rule.text,
                    passed=True,
                    message="level=skip",
                    kind="none",
                    skipped=True,
                    skip_reason="level=skip",
                )
            )
            continue

        # Check if rule is filtered by --only
        if only is not None and rule.id not in only:
            continue  # Silently skip --only filtered

        # Check if rule is filtered by --skip
        if rule.id in skip:
            results.append(
                ProbeResult(
                    rule_id=rule.id,
                    rule_text=rule.text,
                    passed=True,
                    message="--skip flag",
                    kind="none",
                    skipped=True,
                    skip_reason="--skip flag",
                )
            )
            continue

        # No verify = skipped
        if not rule.verify:
            results.append(
                ProbeResult(
                    rule_id=rule.id,
                    rule_text=rule.text,
                    passed=True,
                    message="no verify defined",
                    kind="none",
                    skipped=True,
                    skip_reason="no verify defined",
                )
            )
            continue

        # Verify rule against facts
        verify_result = verify_rule(rule.verify, fact_map)
        results.append(
            ProbeResult(
                rule_id=rule.id,
                rule_text=rule.text,
                passed=verify_result.passed,
                message=verify_result.message or "verified",
                kind="verify",
            )
        )

    return results


__all__ = [
    # Core types
    "Fact",
    "Probe",
    "ProbeConfig",
    "ProbeContext",
    "ProbeResult",
    "ResultFact",
    "generate_id",
    # Probe configs
    "ShellConfig",
    "UrlConfig",
    "LLMConfig",
    "ScanConfig",
    # Probes
    "ShellProbe",
    "UrlProbe",
    "LLMProbe",
    "ScanProbe",
    # Verification
    "Verify",
    "VerifyResult",
    "verify_rule",
    # Registry
    "REGISTRY",
    "parse_probe",
    "get_probe",
    # Main entry point
    "check_spec",
    # Utilities
    "clear_scan_cache",
]
