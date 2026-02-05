"""Check command implementation."""

from __future__ import annotations

from argparse import Namespace
from dataclasses import asdict

from certo.check import CheckResult, check_blueprint
from certo.cli.output import Output, OutputFormat


def cmd_check(args: Namespace, output: Output) -> int:
    """Run verification checks against the blueprint."""
    blueprint_path = args.path / ".certo" / "spec.toml"

    output.verbose_info(f"Checking spec: {blueprint_path}")

    offline = getattr(args, "offline", False)
    no_cache = getattr(args, "no_cache", False)
    model = getattr(args, "model", None)

    if offline:
        output.verbose_info("Running in offline mode (LLM checks will be skipped)")

    results = check_blueprint(
        blueprint_path,
        offline=offline,
        no_cache=no_cache,
        model=model,
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

    # JSON output
    output.json_output(
        {
            "passed": passed,
            "failed": failed,
            "results": [asdict(r) for r in results],
        }
    )

    return 1 if failed > 0 else 0


def _output_check_result(output: Output, result: CheckResult) -> None:
    """Output a single check result."""
    if output.format == OutputFormat.TEXT:
        status = "✓" if result.passed else "✗"
        if result.passed:
            if not output.quiet:
                print(f"{status} [{result.concern_id}] {result.claim}")
                if output.verbose:
                    print(f"    Strategy: {result.strategy}")
                    print(f"    {result.message}")
        else:
            # Always show failures
            print(f"{status} [{result.concern_id}] {result.claim}")
            print(f"    {result.message}")


def _output_summary(output: Output, passed: int, failed: int) -> None:
    """Output summary."""
    if output.format == OutputFormat.TEXT:
        if not output.quiet or failed > 0:
            print()
            print(f"Passed: {passed}, Failed: {failed}")
