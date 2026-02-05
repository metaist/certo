"""Core check types and main entry point."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from certo.spec import Spec


@dataclass
class CheckResult:
    """Result of a single verification check."""

    concern_id: str
    claim: str
    passed: bool
    message: str
    strategy: str


@dataclass
class CheckContext:
    """Context for running checks."""

    project_root: Path
    blueprint_path: Path
    blueprint: Spec | None = None
    offline: bool = False
    no_cache: bool = False
    model: str | None = None


def check_blueprint(
    blueprint_path: Path,
    *,
    offline: bool = False,
    no_cache: bool = False,
    model: str | None = None,
) -> list[CheckResult]:
    """Run all blueprint checks and return results."""
    from certo.check.llm import check_concern_llm
    from certo.check.scan import check_concern_scan
    from certo.check.static import check_blueprint_exists, check_blueprint_valid_toml

    project_root = blueprint_path.parent.parent  # .certo.spec.toml -> project root

    ctx = CheckContext(
        project_root=project_root,
        blueprint_path=blueprint_path,
        offline=offline,
        no_cache=no_cache,
        model=model,
    )

    results: list[CheckResult] = []

    # c1: Spec can be parsed
    exists_result = check_blueprint_exists(ctx)
    if not exists_result.passed:
        results.append(exists_result)
        return results

    toml_result = check_blueprint_valid_toml(ctx)
    results.append(toml_result)

    if not toml_result.passed or ctx.blueprint is None:
        return results

    # Process concerns from blueprint
    for concern in ctx.blueprint.concerns:
        if concern.strategy == "static":
            # Check if we have a handler for this static concern
            if "scan" in concern.verify_with:
                result = check_concern_scan(ctx, concern)
                results.append(result)
            # else: no handler, skip
            continue

        if concern.strategy == "llm":
            # Explicit LLM strategy - verify with LLM
            result = check_concern_llm(ctx, concern)
            results.append(result)
        elif concern.strategy == "auto" and concern.context:
            # Auto strategy with context - try LLM
            result = check_concern_llm(ctx, concern)
            results.append(result)
        # else: auto without context - skip (no way to verify yet)

    return results
