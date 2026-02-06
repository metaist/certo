"""Core check types and main entry point."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from certo.spec import LLMCheck, ShellCheck, Spec


@dataclass
class CheckResult:
    """Result of a single verification check."""

    claim_id: str
    claim_text: str
    passed: bool
    message: str
    strategy: str
    check_id: str = ""  # ID of the specific check (if applicable)
    output: str = ""  # Full command output (for shell checks)


@dataclass
class CheckContext:
    """Context for running checks."""

    project_root: Path
    spec_path: Path
    spec: Spec | None = None
    offline: bool = False
    no_cache: bool = False
    model: str | None = None

    @property
    def root(self) -> Path:
        """Alias for project_root."""
        return self.project_root


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
    from certo.check.llm import run_llm_check
    from certo.check.shell import run_shell_check
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
    skip = skip or set()

    # Built-in: Spec can be parsed (always run unless explicitly skipped)
    if "builtin-spec-valid" not in skip:
        if only is None or "builtin-spec-valid" in only:
            exists_result = check_spec_exists(ctx)
            if not exists_result.passed:
                results.append(exists_result)
                return results

            toml_result = check_spec_valid_toml(ctx)
            results.append(toml_result)

            if not toml_result.passed or ctx.spec is None:
                return results
        elif ctx.spec is None:
            # Need to load spec even if skipping builtin check
            from certo.check.static import check_spec_valid_toml

            check_spec_valid_toml(ctx)
            if ctx.spec is None:
                return results
    else:
        # Load spec even if skipping builtin check
        from certo.check.static import check_spec_valid_toml

        check_spec_valid_toml(ctx)
        if ctx.spec is None:
            return results

    # Process claims from spec
    for claim in ctx.spec.claims:
        # Skip claims that shouldn't be checked
        if claim.status in ("rejected", "superseded"):
            continue
        if claim.level == "skip":
            continue

        # Check if claim is filtered by --only
        if only is not None and claim.id not in only:
            # Check if any of this claim's checks are in --only
            claim_check_ids = {check.id for check in claim.checks if check.id}
            if not claim_check_ids.intersection(only):
                continue

        # Check if claim is filtered by --skip
        if claim.id in skip:
            continue

        # No checks defined = skipped
        if not claim.checks:
            results.append(
                CheckResult(
                    claim_id=claim.id,
                    claim_text=claim.text,
                    passed=True,  # Not a failure, just no checks
                    message="Skipped: no checks defined",
                    strategy="none",
                )
            )
            continue

        # Run each check
        for check in claim.checks:
            check_id = getattr(check, "id", "") or ""

            # Skip this specific check if in skip set
            if check_id and check_id in skip:
                continue

            # If --only specified with check IDs, only run matching checks
            if only is not None and claim.id not in only:
                if not check_id or check_id not in only:
                    continue

            if isinstance(check, ShellCheck):
                result = run_shell_check(ctx, claim, check)
                result.check_id = check_id
                results.append(result)
            elif isinstance(check, LLMCheck):
                result = run_llm_check(ctx, claim, check)
                result.check_id = check_id
                results.append(result)

    return results


# Backward compatibility alias
check_blueprint = check_spec
