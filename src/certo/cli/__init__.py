"""Command-line interface for certo."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from certo.cli.check import cmd_check
from certo.cli.kb import cmd_kb_update
from certo.cli.output import Output, OutputFormat
from certo.cli.plan import cmd_plan_show
from certo.cli.scan import cmd_scan

# Re-export for convenience
__all__ = ["Output", "OutputFormat", "main"]

# Global flags that can appear before or after subcommand
GLOBAL_FLAGS = {"-q", "--quiet", "-v", "--verbose", "--format"}


def _normalize_argv(argv: list[str]) -> list[str]:
    """Move global flags from before subcommand to after.

    This allows: certo -q scan  ->  certo scan -q
    """
    if not argv:
        return argv

    # Find where the subcommand is
    subcommands = {"check", "scan", "kb", "plan"}
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

    # plan command
    plan_parser = subparsers.add_parser("plan", help="view and manage blueprint")

    def cmd_plan_help(args: Namespace, output: Output) -> int:  # noqa: ARG001
        plan_parser.print_help()
        return 0

    plan_parser.set_defaults(func=cmd_plan_help)
    plan_subparsers = plan_parser.add_subparsers(dest="plan_command")

    # plan show command
    plan_show_parser = plan_subparsers.add_parser(
        "show", help="display blueprint contents"
    )
    _add_global_args(plan_show_parser)
    plan_show_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="project root (default: current directory)",
    )
    plan_show_parser.add_argument(
        "id",
        nargs="?",
        help="specific item ID to show (e.g., d1, c3)",
    )
    plan_show_parser.add_argument(
        "--decisions",
        action="store_true",
        help="show only decisions",
    )
    plan_show_parser.add_argument(
        "--concerns",
        action="store_true",
        help="show only concerns",
    )
    plan_show_parser.add_argument(
        "--contexts",
        action="store_true",
        help="show only contexts",
    )
    plan_show_parser.set_defaults(func=cmd_plan_show)

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
