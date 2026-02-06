"""Spec verification checks.

Each check type is self-contained in its own module with both
the configuration dataclass and the runner that operates on it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certo.check.core import Check, CheckContext, CheckResult, Runner, generate_id
from certo.check.fact import FactCheck, FactRunner, clear_scan_cache
from certo.check.llm import LLMCheck, LLMRunner
from certo.check.shell import ShellCheck, ShellRunner
from certo.check.url import UrlCheck, UrlRunner

# Registry mapping kind -> (CheckClass, RunnerInstance)
REGISTRY: dict[str, tuple[type[Check], Runner]] = {
    "shell": (ShellCheck, ShellRunner()),
    "llm": (LLMCheck, LLMRunner()),
    "fact": (FactCheck, FactRunner()),
    "url": (UrlCheck, UrlRunner()),
}


def parse_check(data: dict[str, Any]) -> Check:
    """Parse a check from TOML data, dispatching on kind."""
    kind = data.get("kind", "")
    if kind not in REGISTRY:
        raise ValueError(f"Unknown check kind: {kind}")
    check_cls, _ = REGISTRY[kind]
    return check_cls.parse(data)


def get_runner(kind: str) -> Runner | None:
    """Get the runner for a check kind."""
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
) -> list[CheckResult]:
    """Run all spec checks and return results.

    Args:
        spec_path: Path to spec.toml
        offline: Skip LLM checks
        no_cache: Ignore cached results
        model: LLM model to use
        only: If set, only run checks for these claim/check IDs
        skip: Skip checks for these claim/check IDs
    """
    from certo.spec import Spec

    project_root = spec_path.parent.parent  # .certo/spec.toml -> project root

    ctx = CheckContext(
        project_root=project_root,
        spec_path=spec_path,
        offline=offline,
        no_cache=no_cache,
        model=model,
    )

    results: list[CheckResult] = []
    skip = skip or set()

    # Load spec - fail early if can't parse
    try:
        ctx.spec = Spec.load(spec_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Spec not found: {spec_path}") from None
    except Exception as e:
        raise ValueError(f"Failed to parse spec: {e}") from None

    # Process claims from spec
    for claim in ctx.spec.claims:
        # Skip claims that shouldn't be checked
        if claim.status in ("rejected", "superseded"):
            results.append(
                CheckResult(
                    claim_id=claim.id,
                    claim_text=claim.text,
                    passed=True,
                    message=f"status={claim.status}",
                    kind="none",
                    skipped=True,
                    skip_reason=f"status={claim.status}",
                )
            )
            continue

        if claim.level == "skip":
            results.append(
                CheckResult(
                    claim_id=claim.id,
                    claim_text=claim.text,
                    passed=True,
                    message="level=skip",
                    kind="none",
                    skipped=True,
                    skip_reason="level=skip",
                )
            )
            continue

        # Check if claim is filtered by --only
        if only is not None and claim.id not in only:
            # Check if any of this claim's checks are in --only
            claim_check_ids = {c.id for c in claim.checks if c.id}
            if not claim_check_ids.intersection(only):
                continue  # Silently skip --only filtered (not interesting)

        # Check if claim is filtered by --skip
        if claim.id in skip:
            results.append(
                CheckResult(
                    claim_id=claim.id,
                    claim_text=claim.text,
                    passed=True,
                    message="--skip flag",
                    kind="none",
                    skipped=True,
                    skip_reason="--skip flag",
                )
            )
            continue

        # No checks defined = skipped
        if not claim.checks:
            results.append(
                CheckResult(
                    claim_id=claim.id,
                    claim_text=claim.text,
                    passed=True,
                    message="no checks defined",
                    kind="none",
                    skipped=True,
                    skip_reason="no checks defined",
                )
            )
            continue

        # Run each check
        for check in claim.checks:
            check_id = check.id or ""
            check_status = check.status

            # Skip disabled checks
            if check_status == "disabled":
                results.append(
                    CheckResult(
                        claim_id=claim.id,
                        claim_text=claim.text,
                        passed=True,
                        message="check disabled",
                        kind="none",
                        check_id=check_id,
                        skipped=True,
                        skip_reason="check disabled",
                    )
                )
                continue

            # Skip this specific check if in skip set
            if check_id and check_id in skip:
                results.append(
                    CheckResult(
                        claim_id=claim.id,
                        claim_text=claim.text,
                        passed=True,
                        message="--skip flag",
                        kind="none",
                        check_id=check_id,
                        skipped=True,
                        skip_reason="--skip flag",
                    )
                )
                continue

            # If --only specified with check IDs, only run matching checks
            if only is not None and claim.id not in only:
                if not check_id or check_id not in only:
                    continue  # Silently skip --only filtered

            # Get runner from registry
            runner = get_runner(check.kind)
            if runner is None:  # pragma: no cover
                continue  # Unknown check type - unreachable since Spec.load validates

            result = runner.run(ctx, claim, check)
            result.check_id = check_id
            results.append(result)

    return results


__all__ = [
    # Core types
    "Check",
    "CheckContext",
    "CheckResult",
    "Runner",
    "generate_id",
    # Check types
    "ShellCheck",
    "UrlCheck",
    "LLMCheck",
    "FactCheck",
    # Runners
    "ShellRunner",
    "UrlRunner",
    "LLMRunner",
    "FactRunner",
    # Registry
    "REGISTRY",
    "parse_check",
    "get_runner",
    # Main entry point
    "check_spec",
    # Utilities
    "clear_scan_cache",
]
