"""LLM-based verification checks."""

from __future__ import annotations

from typing import Any

from certo.check.core import CheckContext, CheckResult


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
