"""Core check types and main entry point."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from certo.spec import Spec


@dataclass
class CheckResult:
    """Result of a single verification check."""

    claim_id: str
    claim_text: str
    passed: bool
    message: str
    strategy: str


@dataclass
class CheckContext:
    """Context for running checks."""

    project_root: Path
    spec_path: Path
    spec: Spec | None = None
    offline: bool = False
    no_cache: bool = False
    model: str | None = None


def check_spec(
    spec_path: Path,
    *,
    offline: bool = False,
    no_cache: bool = False,
    model: str | None = None,
) -> list[CheckResult]:
    """Run all spec checks and return results."""
    from certo.check.llm import check_claim_llm
    from certo.check.scan import check_claim_scan
    from certo.check.static import check_spec_exists, check_spec_valid_toml

    project_root = spec_path.parent.parent  # .certo/spec.toml -> project root

    ctx = CheckContext(
        project_root=project_root,
        spec_path=spec_path,
        offline=offline,
        no_cache=no_cache,
        model=model,
    )

    results: list[CheckResult] = []

    # Built-in: Spec can be parsed
    exists_result = check_spec_exists(ctx)
    if not exists_result.passed:
        results.append(exists_result)
        return results

    toml_result = check_spec_valid_toml(ctx)
    results.append(toml_result)

    if not toml_result.passed or ctx.spec is None:
        return results

    # Process claims from spec
    for claim in ctx.spec.claims:
        # Skip claims that shouldn't be checked
        if claim.status in ("rejected", "superseded"):
            continue
        if claim.level == "skip":
            continue

        # Determine verification strategy
        strategies = claim.verify if claim.verify else ["auto"]

        if "scan" in strategies:
            result = check_claim_scan(ctx, claim)
            results.append(result)
        elif "llm" in strategies:
            result = check_claim_llm(ctx, claim)
            results.append(result)
        elif "static" in strategies:
            # No generic static handler yet, skip
            continue
        elif "auto" in strategies and claim.files:
            # Auto with files - try LLM
            result = check_claim_llm(ctx, claim)
            results.append(result)
        # else: auto without files - skip (no way to verify yet)

    return results


# Backward compatibility alias
check_blueprint = check_spec
