"""Command-line interface for certo."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from dataclasses import asdict
from pathlib import Path

from certo.check import CheckResult, check_blueprint
from certo.cli_util import Output, OutputFormat
from certo.scan import scan_project

# Global flags that can appear before or after subcommand
GLOBAL_FLAGS = {"-q", "--quiet", "-v", "--verbose", "--format"}


def _normalize_argv(argv: list[str]) -> list[str]:
    """Move global flags from before subcommand to after.

    This allows: certo -q scan  ->  certo scan -q
    """
    if not argv:
        return argv

    # Find where the subcommand is
    subcommands = {"check", "scan", "kb"}
    cmd_index = None
    for i, arg in enumerate(argv):
        if arg in subcommands:
            cmd_index = i
            break

    if cmd_index is None:
        return argv  # No subcommand found

    # Collect global flags before the subcommand
    global_flags_before: list[str] = []
    other_args_before: list[str] = []

    i = 0
    while i < cmd_index:
        arg = argv[i]
        if arg in GLOBAL_FLAGS:
            global_flags_before.append(arg)
            # Check if this flag takes a value
            if arg == "--format" and i + 1 < cmd_index:
                i += 1
                global_flags_before.append(argv[i])
        elif arg.startswith("--format="):
            global_flags_before.append(arg)
        else:
            other_args_before.append(arg)
        i += 1

    # Reconstruct: other_before + subcommand_and_after + global_flags
    return other_args_before + argv[cmd_index:] + global_flags_before


def cmd_check(args: Namespace, output: Output) -> int:
    """Run verification checks against the blueprint."""
    blueprint_path = args.path / ".certo" / "blueprint.toml"

    output.verbose_info(f"Checking blueprint: {blueprint_path}")

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


def cmd_scan(args: Namespace, output: Output) -> int:
    """Scan project for assumptions and consistency issues."""
    output.verbose_info(f"Scanning project: {args.path}")

    result = scan_project(args.path)

    # Display assumptions
    if result.assumptions:
        output.info("Discovered assumptions:")
        for assumption in result.assumptions:
            status_icon = "✓" if assumption.status == "verified" else "?"
            output.info(f"  [{status_icon}] {assumption.description}")
            if output.verbose:
                for ev in assumption.evidence:
                    output.verbose_info(f"      Evidence: {ev}")
                for match in assumption.should_match:
                    output.verbose_info(f"      Should match: {match}")

    # Display issues
    if result.issues:
        output.info("")
        output.info("Consistency issues:")
        for issue in result.issues:
            icon = "✗" if issue.severity == "error" else "⚠"
            # Always show issues, even in quiet mode
            if output.quiet and output.format == OutputFormat.TEXT:
                print(f"{icon} {issue.message}")
            else:
                output.info(f"  {icon} {issue.message}")
            if output.verbose:
                output.verbose_info(f"      Sources: {', '.join(issue.sources)}")

    # Summary
    if not output.quiet:
        output.info("")
        output.info(
            f"Assumptions: {len(result.assumptions)}, Issues: {len(result.issues)}"
        )

    # JSON output
    output.json_output(
        {
            "assumptions": [
                {
                    "id": a.id,
                    "description": a.description,
                    "category": a.category,
                    "evidence": a.evidence,
                    "should_match": a.should_match,
                    "status": a.status,
                }
                for a in result.assumptions
            ],
            "issues": [
                {
                    "message": i.message,
                    "sources": i.sources,
                    "severity": i.severity,
                }
                for i in result.issues
            ],
        }
    )

    return 1 if result.issues else 0


def cmd_kb_update(args: Namespace, output: Output) -> int:
    """Update knowledge base from authoritative sources."""
    from certo.kb.update import update_all, update_python

    source = getattr(args, "source", None)

    if source == "python":
        output.info("Updating Python knowledge...")
        success = update_python(verbose=output.verbose)
        if success:
            output.info("Python knowledge updated.")
        else:
            output.error("Failed to update Python knowledge.")
            return 1
    else:
        output.info("Updating all knowledge sources...")
        count = update_all(verbose=output.verbose)
        output.info(f"Updated {count} source(s).")

    output.json_output({"updated": source or "all", "success": True})
    return 0


def cmd_version(args: Namespace, output: Output) -> int:  # noqa: ARG001
    """Print version information."""
    from certo import __version__

    if output.format == OutputFormat.JSON:
        output.json_output({"version": __version__})
    else:
        print(f"certo {__version__}")
    return 0


def _add_global_args(parser: ArgumentParser) -> None:
    """Add global arguments to a parser."""
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="only show issues, no output on success",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="show detailed output"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="output format (default: text)",
    )


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    # Normalize argv to move global flags after subcommand
    if argv is None:
        argv = sys.argv[1:]
    argv = _normalize_argv(list(argv))

    parser = ArgumentParser(
        prog="certo",
        description="Turn conversations into verifiable specifications.",
    )
    _add_global_args(parser)

    subparsers = parser.add_subparsers(dest="command")

    # check command
    check_parser = subparsers.add_parser("check", help="verify blueprint against code")
    _add_global_args(check_parser)
    check_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="project root (default: current directory)",
    )
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
    check_parser.set_defaults(func=cmd_check)

    # scan command
    scan_parser = subparsers.add_parser(
        "scan", help="discover assumptions and check consistency"
    )
    _add_global_args(scan_parser)
    scan_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="project root (default: current directory)",
    )
    scan_parser.set_defaults(func=cmd_scan)

    # kb command
    kb_parser = subparsers.add_parser("kb", help="manage knowledge base")

    def cmd_kb_help(args: Namespace, output: Output) -> int:  # noqa: ARG001
        kb_parser.print_help()
        return 0

    kb_parser.set_defaults(func=cmd_kb_help)
    kb_subparsers = kb_parser.add_subparsers(dest="kb_command")

    # kb update command
    kb_update_parser = kb_subparsers.add_parser(
        "update", help="update knowledge from authoritative sources"
    )
    _add_global_args(kb_update_parser)
    kb_update_parser.add_argument(
        "source",
        nargs="?",
        choices=["python"],
        help="specific source to update (default: all)",
    )
    kb_update_parser.set_defaults(func=cmd_kb_update)

    # Parse
    args = parser.parse_args(argv)

    # Create output handler
    output = Output(
        quiet=args.quiet,
        verbose=args.verbose,
        fmt=OutputFormat(args.format),
    )

    try:
        if args.version:
            result = cmd_version(args, output)
        elif args.command is None:
            parser.print_help()
            return 0
        else:
            result = args.func(args, output)

        output.finalize()
        return result
    except Exception as e:
        output.error(f"Error: {e}")
        if output.format == OutputFormat.JSON:
            output.json_output({"error": str(e)})
            output.finalize()
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
