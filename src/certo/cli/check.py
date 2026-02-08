"""Check command implementation."""

from __future__ import annotations

import json
from argparse import ArgumentParser, Namespace, _SubParsersAction
from pathlib import Path
from typing import Any, Callable

from certo.probe import CheckResult, check_spec, parse_check
from certo.cli.output import Output, OutputFormat
from certo.spec import Spec, generate_id


def add_check_parser(
    subparsers: _SubParsersAction[ArgumentParser],
    add_global_args: Callable[[ArgumentParser], None],
) -> None:
    """Add check subcommand and its subparsers."""
    check_parser = subparsers.add_parser("check", help="manage and run checks")
    add_global_args(check_parser)

    # Add run arguments to main check parser for backward compatibility
    # (certo check --offline should work the same as certo check run --offline)
    check_parser.add_argument(
        "--offline",
        action="store_true",
        help="skip LLM-backed checks (no network calls)",
    )
    check_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="ignore cached verification results",
    )
    check_parser.add_argument(
        "--model",
        help="LLM model to use (overrides CERTO_MODEL env var)",
    )
    check_parser.add_argument(
        "--only",
        help="run only specific claims/checks (comma-separated IDs)",
    )
    check_parser.add_argument(
        "--skip",
        help="skip specific claims/checks (comma-separated IDs)",
    )
    check_parser.add_argument(
        "--output",
        metavar="PATH",
        help="write detailed results to file (use - for stdout)",
    )

    check_subparsers = check_parser.add_subparsers(dest="check_command")

    # check run (default behavior, runs checks)
    run_parser = check_subparsers.add_parser("run", help="run verification checks")
    add_global_args(run_parser)
    run_parser.add_argument(
        "--offline",
        action="store_true",
        help="skip LLM-backed checks (no network calls)",
    )
    run_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="ignore cached verification results",
    )
    run_parser.add_argument(
        "--model",
        help="LLM model to use (overrides CERTO_MODEL env var)",
    )
    run_parser.add_argument(
        "--only",
        help="run only specific claims/checks (comma-separated IDs)",
    )
    run_parser.add_argument(
        "--skip",
        help="skip specific claims/checks (comma-separated IDs)",
    )
    run_parser.add_argument(
        "--output",
        metavar="PATH",
        help="write detailed results to file (use - for stdout)",
    )
    run_parser.set_defaults(func=cmd_check_run)

    # check list
    list_parser = check_subparsers.add_parser("list", help="list all checks")
    add_global_args(list_parser)
    list_parser.add_argument(
        "--status",
        choices=["enabled", "disabled"],
        help="filter by status",
    )
    list_parser.add_argument(
        "--kind",
        choices=["shell", "llm", "fact", "url"],
        help="filter by check kind",
    )
    list_parser.set_defaults(func=cmd_check_list)

    # check show
    show_parser = check_subparsers.add_parser("show", help="show check details")
    add_global_args(show_parser)
    show_parser.add_argument("id", help="check ID")
    show_parser.set_defaults(func=cmd_check_show)

    # check add
    add_parser = check_subparsers.add_parser("add", help="add a new check")
    add_global_args(add_parser)
    add_parser.add_argument(
        "kind", choices=["shell", "llm", "fact", "url"], help="check kind"
    )
    add_parser.add_argument("--id", help="check ID (auto-generated if not provided)")
    add_parser.add_argument(
        "--status", choices=["enabled", "disabled"], default="enabled"
    )
    # Shell check options
    add_parser.add_argument("--cmd", help="shell command (for shell checks)")
    add_parser.add_argument(
        "--exit-code", type=int, default=0, help="expected exit code (for shell checks)"
    )
    add_parser.add_argument(
        "--matches", help="comma-separated patterns that must match (for shell checks)"
    )
    add_parser.add_argument(
        "--timeout", type=int, default=60, help="timeout in seconds (for shell checks)"
    )
    # LLM check options
    add_parser.add_argument(
        "--files", help="comma-separated file patterns (for llm checks)"
    )
    add_parser.add_argument("--prompt", help="verification prompt (for llm checks)")
    # Fact check options
    add_parser.add_argument("--has", help="fact key that must exist (for fact checks)")
    add_parser.add_argument(
        "--empty", help="fact key that must be empty (for fact checks)"
    )
    add_parser.add_argument(
        "--equals", help="fact key that must equal --value (for fact checks)"
    )
    add_parser.add_argument("--value", help="expected value for --equals")
    # URL check options
    add_parser.add_argument("--url", help="URL to fetch (for url checks)")
    add_parser.set_defaults(func=cmd_check_add)

    # check remove
    remove_parser = check_subparsers.add_parser("remove", help="remove a check")
    add_global_args(remove_parser)
    remove_parser.add_argument("id", help="check ID")
    remove_parser.set_defaults(func=cmd_check_remove)

    # check on (enable)
    on_parser = check_subparsers.add_parser("on", help="enable a check")
    add_global_args(on_parser)
    on_parser.add_argument("id", help="check ID")
    on_parser.set_defaults(func=cmd_check_on)

    # check off (disable)
    off_parser = check_subparsers.add_parser("off", help="disable a check")
    add_global_args(off_parser)
    off_parser.add_argument("id", help="check ID")
    off_parser.set_defaults(func=cmd_check_off)

    # Default: if no subcommand, run checks (backward compat)
    def cmd_check_default(args: Namespace, output: Output) -> int:
        # If no subcommand specified, run checks
        return cmd_check_run(args, output)

    check_parser.set_defaults(func=cmd_check_default)


def cmd_check_run(args: Namespace, output: Output) -> int:
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
        claim_results[result.rule_id].append(result)

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
        claim_text = claim_checks[0].rule_text

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


def cmd_check_list(args: Namespace, output: Output) -> int:
    """List all checks."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)

    # Filter checks
    status_filter = getattr(args, "status", None)
    kind_filter = getattr(args, "kind", None)

    checks = spec.checks
    if status_filter:
        checks = [c for c in checks if c.status == status_filter]
    if kind_filter:
        checks = [c for c in checks if c.kind == kind_filter]

    if not checks:
        output.info("No checks found")
        output.json_output({"checks": []})
        return 0

    for check in checks:
        _print_check_summary(check, output)

    output.json_output(
        {"checks": [{"id": c.id, "kind": c.kind, "status": c.status} for c in checks]}
    )

    return 0


def cmd_check_show(args: Namespace, output: Output) -> int:
    """Show check details."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    check = spec.get_check(args.id)

    if not check:
        output.error(f"Check not found: {args.id}")
        return 1

    _print_check_detail(check, output)

    # Build JSON output
    check_dict: dict[str, Any] = {
        "id": check.id,
        "kind": check.kind,
        "status": check.status,
    }

    # Add kind-specific fields
    from certo.probe.shell import ShellCheck
    from certo.probe.llm import LLMCheck
    from certo.probe.fact import FactCheck
    from certo.probe.url import UrlCheck

    # Note: UrlCheck must come before ShellCheck (UrlCheck extends ShellCheck)
    match check:
        case UrlCheck():
            check_dict["url"] = check.url
            check_dict["cmd"] = check.cmd
        case ShellCheck():
            check_dict["cmd"] = check.cmd
            check_dict["exit_code"] = check.exit_code
            check_dict["matches"] = check.matches
            check_dict["timeout"] = check.timeout
        case LLMCheck():
            check_dict["files"] = check.files
            check_dict["prompt"] = check.prompt
        case FactCheck():
            check_dict["has"] = check.has
            check_dict["empty"] = check.empty
            check_dict["equals"] = check.equals
            check_dict["value"] = check.value

    output.json_output(check_dict)

    return 0


def cmd_check_add(args: Namespace, output: Output) -> int:
    """Add a new check."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)

    # Build check data based on kind
    check_data: dict[str, Any] = {
        "kind": args.kind,
        "status": args.status,
    }

    match args.kind:
        case "shell":
            if not args.cmd:
                output.error("Shell checks require --cmd")
                return 1
            check_data["cmd"] = args.cmd
            check_data["exit_code"] = args.exit_code
            if args.matches:
                check_data["matches"] = [m.strip() for m in args.matches.split(",")]
            check_data["timeout"] = args.timeout
            # Generate ID from cmd if not provided
            if args.id:
                check_data["id"] = args.id
            else:
                check_data["id"] = generate_id("k", f"shell:{args.cmd}")

        case "llm":
            if not args.files:
                output.error("LLM checks require --files")
                return 1
            check_data["files"] = [f.strip() for f in args.files.split(",")]
            if args.prompt:
                check_data["prompt"] = args.prompt
            if args.id:
                check_data["id"] = args.id
            else:
                check_data["id"] = generate_id("k", f"llm:{args.files}")

        case "fact":
            if not any([args.has, args.empty, args.equals]):
                output.error("Fact checks require --has, --empty, or --equals")
                return 1
            if args.has:
                check_data["has"] = args.has
            if args.empty:
                check_data["empty"] = args.empty
            if args.equals:
                if not args.value:
                    output.error("--equals requires --value")
                    return 1
                check_data["equals"] = args.equals
                check_data["value"] = args.value
            if args.id:
                check_data["id"] = args.id
            else:
                key = args.has or args.empty or args.equals
                check_data["id"] = generate_id("k", f"fact:{key}")

        case "url":
            if not args.url:
                output.error("URL checks require --url")
                return 1
            check_data["url"] = args.url
            if args.cmd:
                check_data["cmd"] = args.cmd
            if args.id:
                check_data["id"] = args.id
            else:
                check_data["id"] = generate_id("k", f"url:{args.url}")

    # Check for existing check with same ID
    check_id = check_data["id"]
    if spec.get_check(check_id):
        output.error(f"Check already exists: {check_id}")
        return 1

    # Parse and add check
    check = parse_check(check_data)
    spec.checks.append(check)
    spec.save(spec_path)

    output.success(f"Added check: {check_id}")
    output.json_output({"id": check_id, "kind": args.kind, "status": args.status})

    return 0


def cmd_check_remove(args: Namespace, output: Output) -> int:
    """Remove a check."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    check = spec.get_check(args.id)

    if not check:
        output.error(f"Check not found: {args.id}")
        return 1

    spec.checks = [c for c in spec.checks if c.id != args.id]
    spec.save(spec_path)

    output.success(f"Removed check: {args.id}")
    output.json_output({"id": args.id, "removed": True})

    return 0


def cmd_check_on(args: Namespace, output: Output) -> int:
    """Enable a check."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    check = spec.get_check(args.id)

    if not check:
        output.error(f"Check not found: {args.id}")
        return 1

    if check.status == "enabled":
        output.info(f"Check already enabled: {args.id}")
        return 0

    check.status = "enabled"
    spec.save(spec_path)

    output.success(f"Enabled check: {args.id}")
    output.json_output({"id": args.id, "status": "enabled"})

    return 0


def cmd_check_off(args: Namespace, output: Output) -> int:
    """Disable a check."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    check = spec.get_check(args.id)

    if not check:
        output.error(f"Check not found: {args.id}")
        return 1

    if check.status == "disabled":
        output.info(f"Check already disabled: {args.id}")
        return 0

    check.status = "disabled"
    spec.save(spec_path)

    output.success(f"Disabled check: {args.id}")
    output.json_output({"id": args.id, "status": "disabled"})

    return 0


def _print_check_summary(check: Any, output: Output) -> None:
    """Print a one-line check summary."""
    if output.quiet:
        return

    status_marker = "" if check.status == "enabled" else " [disabled]"
    print(f"{check.id}  [{check.kind}]{status_marker}")


def _print_check_detail(check: Any, output: Output) -> None:
    """Print detailed check info."""
    if output.quiet:
        return

    from certo.probe.shell import ShellCheck
    from certo.probe.llm import LLMCheck
    from certo.probe.fact import FactCheck
    from certo.probe.url import UrlCheck

    print(f"ID:     {check.id}")
    print(f"Kind:   {check.kind}")
    print(f"Status: {check.status}")

    # Note: UrlCheck must come before ShellCheck (UrlCheck extends ShellCheck)
    match check:
        case UrlCheck():
            print(f"URL:    {check.url}")
            if check.cmd:
                print(f"Cmd:    {check.cmd}")
        case ShellCheck():
            print(f"Cmd:    {check.cmd}")
            if check.exit_code != 0:
                print(f"Exit:   {check.exit_code}")
            if check.matches:
                print(f"Match:  {check.matches}")
            if check.timeout != 60:
                print(f"Timeout: {check.timeout}s")
        case LLMCheck():
            print(f"Files:  {check.files}")
            if check.prompt:
                print(f"Prompt: {check.prompt}")
        case FactCheck():
            if check.has:
                print(f"Has:    {check.has}")
            if check.empty:
                print(f"Empty:  {check.empty}")
            if check.equals:
                print(f"Equals: {check.equals} = {check.value}")


def _result_to_dict(result: CheckResult) -> dict[str, Any]:
    """Convert CheckResult to dict, including all fields."""
    return {
        "rule_id": result.rule_id,
        "rule_text": result.rule_text,
        "passed": result.passed,
        "message": result.message,
        "kind": result.kind,
        "probe_id": result.probe_id,
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
    if skipped and len(checks) == 1 and not checks[0].probe_id:
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
                not result.passed and not result.skipped and not result.probe_id
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
    if not result.probe_id:  # pragma: no cover
        return

    if result.skipped:
        if output.verbose:
            print(f"  ⊘ {result.probe_id} [{result.kind}] ({result.skip_reason})")
    elif result.passed:
        if not output.quiet:
            cached = " (cached)" if "(cached)" in result.message else ""
            print(f"  ✓ {result.probe_id} [{result.kind}]{cached}")
    else:
        # Always show failures
        print(f"  ✗ {result.probe_id} [{result.kind}] {result.message}")


def _output_summary(output: Output, passed: int, failed: int, skipped: int) -> None:
    """Output summary."""
    if output.format == OutputFormat.TEXT:
        if not output.quiet or failed > 0:
            print()
            summary = f"Passed: {passed}, Failed: {failed}"
            if skipped > 0:
                summary += f", Skipped: {skipped}"
            print(summary)


# For backward compatibility - expose cmd_check as alias for cmd_check_run
cmd_check = cmd_check_run
