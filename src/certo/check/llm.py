"""LLM-based verification checks."""

from __future__ import annotations

from certo.check.core import CheckContext, CheckResult
from certo.spec import Claim, LLMCheck


def run_llm_check(ctx: CheckContext, claim: Claim, check: LLMCheck) -> CheckResult:
    """Verify a claim using LLM."""
    from certo.llm.provider import LLMError, NoAPIKeyError
    from certo.llm.verify import (
        FileMissingError,
        FileTooLargeError,
        verify_concern,
    )

    # Validate claim has required fields
    if not claim.text:
        return CheckResult(
            claim_id=claim.id,
            claim_text="(no claim text specified)",
            passed=False,
            message="Claim is missing 'text' field",
            strategy="llm",
        )

    if not check.files:
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=False,
            message="LLM check is missing 'files' field",
            strategy="llm",
        )

    # Check offline mode
    if ctx.offline:
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=True,  # Pass in offline mode (not a failure)
            message="Skipped: offline mode",
            strategy="llm",
        )

    # Use custom prompt if provided, otherwise use claim text
    prompt = check.prompt if check.prompt else claim.text

    try:
        result = verify_concern(
            concern_id=claim.id,
            claim=prompt,
            context_patterns=check.files,
            project_root=ctx.project_root,
            model=ctx.model,
            no_cache=ctx.no_cache,
        )

        cache_note = " (cached)" if result.cached else ""
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=result.passed,
            message=f"{result.explanation}{cache_note}",
            strategy="llm",
        )

    except NoAPIKeyError as e:
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=False,
            message=f"API key error: {e}",
            strategy="llm",
        )

    except FileMissingError as e:
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=False,
            message=f"Missing context: {e}",
            strategy="llm",
        )

    except FileTooLargeError as e:
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=False,
            message=f"Context too large: {e}",
            strategy="llm",
        )

    except LLMError as e:
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=False,
            message=f"LLM error: {e}",
            strategy="llm",
        )
