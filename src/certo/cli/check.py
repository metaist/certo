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
        output.verbose_info("Running in offline mode (LLM checks will be skipped)")

    if only:
        output.verbose_info(f"Running only: {', '.join(only)}")

    if skip:
        output.verbose_info(f"Skipping: {', '.join(skip)}")

    results = check_spec(
        spec_path,
        offline=offline,
        no_cache=no_cache,
        model=model,
        only=only,
        skip=skip,
    )

    # Display results
    passed = 0
    failed = 0
    for result in results:
        _output_check_result(output, result)
        if result.passed:
            passed += 1
        else:
            failed += 1

    _output_summary(output, passed, failed)

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
        "strategy": result.strategy,
        "check_id": result.check_id,
        "output": result.output,
    }


def _write_output(output_path: str, data: dict[str, Any]) -> None:
    """Write detailed results to file or stdout."""
    content = json.dumps(data, indent=2, default=str)
    if output_path == "-":
        print(content)
    else:
        Path(output_path).write_text(content)


def _output_check_result(output: Output, result: CheckResult) -> None:
    """Output a single check result."""
    if output.format == OutputFormat.TEXT:
        status = "✓" if result.passed else "✗"
        if result.passed:
            if not output.quiet:
                print(f"{status} [{result.claim_id}] {result.claim_text}")
                if output.verbose:
                    print(f"    Strategy: {result.strategy}")
                    print(f"    {result.message}")
        else:
            # Always show failures
            print(f"{status} [{result.claim_id}] {result.claim_text}")
            print(f"    {result.message}")


def _output_summary(output: Output, passed: int, failed: int) -> None:
    """Output summary."""
    if output.format == OutputFormat.TEXT:
        if not output.quiet or failed > 0:
            print()
            print(f"Passed: {passed}, Failed: {failed}")
