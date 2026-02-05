"""LLM-based verification checks."""

from __future__ import annotations

from certo.spec import Concern
from certo.check.core import CheckContext, CheckResult


def check_concern_llm(ctx: CheckContext, concern: Concern) -> CheckResult:
    """Verify a concern using LLM."""
    from certo.llm.provider import LLMError, NoAPIKeyError
    from certo.llm.verify import (
        FileMissingError,
        FileTooLargeError,
        verify_concern,
    )

    # Validate concern has required fields
    if not concern.claim:
        return CheckResult(
            concern_id=concern.id,
            claim="(no claim specified)",
            passed=False,
            message="Concern is missing 'claim' field",
            strategy="llm",
        )

    if not concern.context:
        return CheckResult(
            concern_id=concern.id,
            claim=concern.claim,
            passed=False,
            message="Concern is missing 'context' field (required for LLM strategy)",
            strategy="llm",
        )

    # Check offline mode
    if ctx.offline:
        return CheckResult(
            concern_id=concern.id,
            claim=concern.claim,
            passed=True,  # Pass in offline mode (not a failure)
            message="Skipped: offline mode",
            strategy="llm",
        )

    try:
        result = verify_concern(
            concern_id=concern.id,
            claim=concern.claim,
            context_patterns=concern.context,
            project_root=ctx.project_root,
            model=ctx.model,
            no_cache=ctx.no_cache,
        )

        cache_note = " (cached)" if result.cached else ""
        return CheckResult(
            concern_id=concern.id,
            claim=concern.claim,
            passed=result.passed,
            message=f"{result.explanation}{cache_note}",
            strategy="llm",
        )

    except NoAPIKeyError as e:
        return CheckResult(
            concern_id=concern.id,
            claim=concern.claim,
            passed=False,
            message=f"API key error: {e}",
            strategy="llm",
        )

    except FileMissingError as e:
        return CheckResult(
            concern_id=concern.id,
            claim=concern.claim,
            passed=False,
            message=f"Missing context: {e}",
            strategy="llm",
        )

    except FileTooLargeError as e:
        return CheckResult(
            concern_id=concern.id,
            claim=concern.claim,
            passed=False,
            message=f"Context too large: {e}",
            strategy="llm",
        )

    except LLMError as e:
        return CheckResult(
            concern_id=concern.id,
            claim=concern.claim,
            passed=False,
            message=f"LLM error: {e}",
            strategy="llm",
        )
