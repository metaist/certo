"""Scan-based verification checks."""

from __future__ import annotations

from certo.check.core import CheckContext, CheckResult
from certo.spec import Claim


def check_claim_scan(ctx: CheckContext, claim: Claim) -> CheckResult:
    """Verify a claim using scan results."""
    from certo.scan import scan_project

    # Run scan
    scan_result = scan_project(ctx.project_root)

    # Check for issues - any issue means the claim failed
    if scan_result.issues:
        messages = [issue.message for issue in scan_result.issues]
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=False,
            message=f"Scan found issues: {'; '.join(messages)}",
            strategy="scan",
        )

    # No issues - check if we found relevant assumptions
    if scan_result.assumptions:
        assumption = scan_result.assumptions[0]  # Primary assumption
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=assumption.status == "verified",
            message=f"{assumption.description} ({assumption.status})",
            strategy="scan",
        )

    return CheckResult(
        claim_id=claim.id,
        claim_text=claim.text,
        passed=True,
        message="No issues found",
        strategy="scan",
    )


# Backward compatibility alias
check_concern_scan = check_claim_scan
