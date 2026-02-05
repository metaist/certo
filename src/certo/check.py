"""Blueprint verification checks."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
    blueprint: dict[str, Any] | None = None
    offline: bool = False
    no_cache: bool = False
    model: str | None = None


def check_blueprint_exists(ctx: CheckContext) -> CheckResult:
    """Check that a blueprint file exists."""
    if ctx.blueprint_path.exists():
        return CheckResult(
            concern_id="c1",
            claim="A blueprint.toml file can be parsed",
            passed=True,
            message="File exists",
            strategy="static",
        )
    return CheckResult(
        concern_id="c1",
        claim="A blueprint.toml file can be parsed",
        passed=False,
        message=f"File not found: {ctx.blueprint_path}",
        strategy="static",
    )


def check_blueprint_valid_toml(ctx: CheckContext) -> CheckResult:
    """Check that the blueprint is valid TOML."""
    if not ctx.blueprint_path.exists():
        return CheckResult(
            concern_id="c1",
            claim="A blueprint.toml file can be parsed",
            passed=False,
            message="Cannot check TOML validity: file does not exist",
            strategy="static",
        )

    try:
        with ctx.blueprint_path.open("rb") as f:
            ctx.blueprint = tomllib.load(f)
        return CheckResult(
            concern_id="c1",
            claim="A blueprint.toml file can be parsed",
            passed=True,
            message="Valid TOML",
            strategy="static",
        )
    except tomllib.TOMLDecodeError as e:
        return CheckResult(
            concern_id="c1",
            claim="A blueprint.toml file can be parsed",
            passed=False,
            message=f"Invalid TOML: {e}",
            strategy="static",
        )


def check_concern_llm(ctx: CheckContext, concern: dict[str, Any]) -> CheckResult:
    """Verify a concern using LLM."""
    from certo.llm.provider import LLMError, NoAPIKeyError
    from certo.llm.verify import (
        FileMissingError,
        FileTooLargeError,
        verify_concern,
    )

    concern_id = concern.get("id", "unknown")
    claim = concern.get("claim", "")
    context_patterns = concern.get("context", [])

    # Validate concern has required fields
    if not claim:
        return CheckResult(
            concern_id=concern_id,
            claim="(no claim specified)",
            passed=False,
            message="Concern is missing 'claim' field",
            strategy="llm",
        )

    if not context_patterns:
        return CheckResult(
            concern_id=concern_id,
            claim=claim,
            passed=False,
            message="Concern is missing 'context' field (required for LLM strategy)",
            strategy="llm",
        )

    # Check offline mode
    if ctx.offline:
        return CheckResult(
            concern_id=concern_id,
            claim=claim,
            passed=True,  # Pass in offline mode (not a failure)
            message="Skipped: offline mode",
            strategy="llm",
        )

    try:
        result = verify_concern(
            concern_id=concern_id,
            claim=claim,
            context_patterns=context_patterns,
            project_root=ctx.project_root,
            model=ctx.model,
            no_cache=ctx.no_cache,
        )

        cache_note = " (cached)" if result.cached else ""
        return CheckResult(
            concern_id=concern_id,
            claim=claim,
            passed=result.passed,
            message=f"{result.explanation}{cache_note}",
            strategy="llm",
        )

    except NoAPIKeyError as e:
        return CheckResult(
            concern_id=concern_id,
            claim=claim,
            passed=False,
            message=f"API key error: {e}",
            strategy="llm",
        )

    except FileMissingError as e:
        return CheckResult(
            concern_id=concern_id,
            claim=claim,
            passed=False,
            message=f"Missing context: {e}",
            strategy="llm",
        )

    except FileTooLargeError as e:
        return CheckResult(
            concern_id=concern_id,
            claim=claim,
            passed=False,
            message=f"Context too large: {e}",
            strategy="llm",
        )

    except LLMError as e:
        return CheckResult(
            concern_id=concern_id,
            claim=claim,
            passed=False,
            message=f"LLM error: {e}",
            strategy="llm",
        )


def check_blueprint(
    blueprint_path: Path,
    *,
    offline: bool = False,
    no_cache: bool = False,
    model: str | None = None,
) -> list[CheckResult]:
    """Run all blueprint checks and return results."""
    project_root = blueprint_path.parent.parent  # .certo/blueprint.toml -> project root

    ctx = CheckContext(
        project_root=project_root,
        blueprint_path=blueprint_path,
        offline=offline,
        no_cache=no_cache,
        model=model,
    )

    results: list[CheckResult] = []

    # c1: Blueprint can be parsed
    exists_result = check_blueprint_exists(ctx)
    if not exists_result.passed:
        results.append(exists_result)
        return results

    toml_result = check_blueprint_valid_toml(ctx)
    results.append(toml_result)

    if not toml_result.passed or ctx.blueprint is None:
        return results

    # Process concerns from blueprint
    concerns = ctx.blueprint.get("concerns", [])
    for concern in concerns:
        strategy = concern.get("strategy", "auto")
        has_context = bool(concern.get("context"))

        if strategy == "static":
            # Static concerns need custom handlers (not implemented yet)
            continue

        if strategy == "llm":
            # Explicit LLM strategy - verify with LLM
            result = check_concern_llm(ctx, concern)
            results.append(result)
        elif strategy == "auto" and has_context:
            # Auto strategy with context - try LLM
            result = check_concern_llm(ctx, concern)
            results.append(result)
        # else: auto without context - skip (no way to verify yet)

    return results
