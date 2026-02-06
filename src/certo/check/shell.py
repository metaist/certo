"""Shell command verification checks."""

from __future__ import annotations

import re
import subprocess

from certo.check.core import CheckContext, CheckResult
from certo.spec import Claim, ShellCheck


def run_shell_check(ctx: CheckContext, claim: Claim, check: ShellCheck) -> CheckResult:
    """Run a shell command and verify the result."""
    if not check.cmd:
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=False,
            message="Shell check has no command",
            strategy="shell",
        )

    try:
        result = subprocess.run(
            check.cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=check.timeout,
            cwd=ctx.root,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=False,
            message=f"Command timed out after {check.timeout}s",
            strategy="shell",
        )
    except Exception as e:
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=False,
            message=f"Command failed: {e}",
            strategy="shell",
        )

    # Combine stdout and stderr
    output = result.stdout + result.stderr

    # Check exit code
    if result.returncode != check.exit_code:
        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=False,
            message=(
                f"Expected exit code {check.exit_code}, "
                f"got {result.returncode}\n{output}"
            ),
            strategy="shell",
        )

    # Check matches (regex patterns that must appear)
    for pattern in check.matches:
        if not re.search(pattern, output):
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=False,
                message=f"Pattern not found: {pattern}\n{output}",
                strategy="shell",
            )

    # Check not_matches (regex patterns that must NOT appear)
    for pattern in check.not_matches:
        if re.search(pattern, output):
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=False,
                message=f"Forbidden pattern found: {pattern}\n{output}",
                strategy="shell",
            )

    return CheckResult(
        claim_id=claim.id,
        claim_text=claim.text,
        passed=True,
        message="Shell check passed",
        strategy="shell",
    )
