"""Scan-based verification checks."""

from __future__ import annotations

from typing import Any

from certo.check.core import CheckContext, CheckResult


def check_concern_scan(ctx: CheckContext, concern: dict[str, Any]) -> CheckResult:
    """Verify a concern using scan results."""
    from certo.scan import scan_project

    concern_id = concern.get("id", "unknown")
    claim = concern.get("claim", "")

    # Run scan
    scan_result = scan_project(ctx.project_root)

    # Check for issues - any issue means the concern failed
    if scan_result.issues:
        messages = [issue.message for issue in scan_result.issues]
        return CheckResult(
            concern_id=concern_id,
            claim=claim,
            passed=False,
            message=f"Scan found issues: {'; '.join(messages)}",
            strategy="scan",
        )

    # No issues - check if we found relevant assumptions
    if scan_result.assumptions:
        assumption = scan_result.assumptions[0]  # Primary assumption
        return CheckResult(
            concern_id=concern_id,
            claim=claim,
            passed=assumption.status == "verified",
            message=f"{assumption.description} ({assumption.status})",
            strategy="scan",
        )

    return CheckResult(
        concern_id=concern_id,
        claim=claim,
        passed=True,
        message="No issues found",
        strategy="scan",
    )
