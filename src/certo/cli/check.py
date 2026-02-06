"""Check command implementation."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import Any

from certo.check import CheckResult, check_spec
from certo.cli.output import Output, OutputFormat


def cmd_check(args: Namespace, output: Output) -> int:
    """Run verification checks against the spec."""
    spec_path = args.path / ".certo" / "spec.toml"

    output.verbose_info(f"Checking spec: {spec_path}")

    offline = getattr(args, "offline", False)
    no_cache = getattr(args, "no_cache", False)
    model = getattr(args, "model", None)

    # Parse --only and --skip
    only_arg = getattr(args, "only", None)
    skip_arg = getattr(args, "skip", None)
    only = set(only_arg.split(",")) if only_arg else None
    skip = set(skip_arg.split(",")) if skip_arg else None

    # Get --output path
    output_path = getattr(args, "output", None)

    if offline:
        output.verbose_info(
            "Running in offline mode (using cached results where available)"
        )

    if only:
        output.verbose_info(f"Running only: {', '.join(only)}")

    if skip:
        output.verbose_info(f"Skipping: {', '.join(skip)}")

    try:
        results = check_spec(
            spec_path,
            offline=offline,
            no_cache=no_cache,
            model=model,
            only=only,
            skip=skip,
        )
    except (FileNotFoundError, ValueError) as e:
        output.error(str(e))
        output.json_output(
            {"error": str(e), "passed": 0, "failed": 1, "skipped": 0, "results": []}
        )
        return 1

    # Group results by claim
    from collections import defaultdict

    claim_results: dict[str, list[CheckResult]] = defaultdict(list)
    for result in results:
        claim_results[result.claim_id].append(result)

    # Display results grouped by claim
    passed = 0
    failed = 0
    skipped = 0

    for claim_id, claim_checks in claim_results.items():
        # Determine overall claim status
        claim_skipped = all(r.skipped for r in claim_checks)
        claim_failed = any(not r.passed and not r.skipped for r in claim_checks)
        claim_passed = not claim_failed and not claim_skipped

        # Get claim text from first result
        claim_text = claim_checks[0].claim_text

        # Count for summary (count claims, not individual checks)
        if claim_skipped:
            skipped += 1
        elif claim_failed:
            failed += 1
        else:
            passed += 1

        # Output claim line with status
        _output_claim(
            output,
            claim_id,
            claim_text,
            claim_passed,
            claim_failed,
            claim_skipped,
            claim_checks,
        )

    _output_summary(output, passed, failed, skipped)

    # Prepare result data
    result_data = {
        "passed": passed,
        "failed": failed,
        "results": [_result_to_dict(r) for r in results],
    }

    # JSON output
    output.json_output(result_data)

    # Write detailed output to file if requested
    if output_path:
        _write_output(output_path, result_data)

    return 1 if failed > 0 else 0


def _result_to_dict(result: CheckResult) -> dict[str, Any]:
    """Convert CheckResult to dict, including all fields."""
    return {
        "claim_id": result.claim_id,
        "claim_text": result.claim_text,
        "passed": result.passed,
        "message": result.message,
        "kind": result.kind,
        "check_id": result.check_id,
        "output": result.output,
        "skipped": result.skipped,
        "skip_reason": result.skip_reason,
    }


def _write_output(output_path: str, data: dict[str, Any]) -> None:
    """Write detailed results to file or stdout."""
    content = json.dumps(data, indent=2, default=str)
    if output_path == "-":
        print(content)
    else:
        Path(output_path).write_text(content)


def _output_claim(
    output: Output,
    claim_id: str,
    claim_text: str,
    passed: bool,
    failed: bool,
    skipped: bool,
    checks: list[CheckResult],
) -> None:
    """Output a claim and its checks."""
    if output.format != OutputFormat.TEXT:
        return

    # Determine status icon
    if skipped:
        icon = "⊘"
    elif failed:
        icon = "✗"
    else:
        icon = "✓"

    # For skipped claims (no checks or level=skip), show reason
    if skipped and len(checks) == 1 and not checks[0].check_id:
        skip_reason = checks[0].skip_reason
        if output.verbose or failed:
            print(f"{icon} [{claim_id}] {claim_text} ({skip_reason})")
        return

    # Show claim line (unless quiet and passed)
    if not output.quiet or failed:
        print(f"{icon} [{claim_id}] {claim_text}")

    # For failures without check_id, show the message
    if failed:
        for result in checks:
            if (
                not result.passed and not result.skipped and not result.check_id
            ):  # pragma: no cover
                print(f"    {result.message}")

    # Show individual checks
    for result in checks:
        _output_check_result(output, result)


def _output_check_result(output: Output, result: CheckResult) -> None:
    """Output a single check result (indented under claim)."""
    if output.format != OutputFormat.TEXT:  # pragma: no cover
        return

    # Skip claim-level results without check_id (already shown in claim line)
    if not result.check_id:  # pragma: no cover
        return

    if result.skipped:
        if output.verbose:
            print(f"  ⊘ {result.check_id} [{result.kind}] ({result.skip_reason})")
    elif result.passed:
        if not output.quiet:
            cached = " (cached)" if "(cached)" in result.message else ""
            print(f"  ✓ {result.check_id} [{result.kind}]{cached}")
    else:
        # Always show failures
        print(f"  ✗ {result.check_id} [{result.kind}] {result.message}")


def _output_summary(output: Output, passed: int, failed: int, skipped: int) -> None:
    """Output summary."""
    if output.format == OutputFormat.TEXT:
        if not output.quiet or failed > 0:
            print()
            summary = f"Passed: {passed}, Failed: {failed}"
            if skipped > 0:
                summary += f", Skipped: {skipped}"
            print(summary)
