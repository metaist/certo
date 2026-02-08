"""Command-line interface for certo."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from certo.cli.check import add_check_parser
from certo.cli.claim import add_claim_parser
from certo.cli.init import cmd_init

from certo.cli.kb import cmd_kb_update
from certo.cli.output import Output, OutputFormat
from certo.cli.scan import cmd_scan
from certo.cli.status import cmd_status

# Re-export for convenience
__all__ = ["Output", "OutputFormat", "main"]

# Global flags that can appear before or after subcommand
GLOBAL_FLAGS = {"-q", "--quiet", "-v", "--verbose", "--format", "--config", "--path"}

# Cached parser for performance (built once, reused)
_PARSER: ArgumentParser | None = None


def _normalize_argv(argv: list[str]) -> list[str]:
    """Move global flags from before subcommand to after.

    This allows: certo -q scan  ->  certo scan -q
    """
    if not argv:
        return argv

    # Find where the subcommand is
    subcommands = {"init", "check", "scan", "kb", "status", "claim"}
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
            if arg in ("--format", "--config", "--path") and i + 1 < cmd_index:
                i += 1
                global_flags_before.append(argv[i])
        elif arg.startswith(("--format=", "--config=", "--path=")):
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
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="path to certo.toml or - for stdin (default: find in parent dirs)",
    )
    # Keep --path as hidden alias for backward compat during transition
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="DEPRECATED: use --config instead",
    )


def _build_parser() -> ArgumentParser:
    """Build the argument parser (cached for performance)."""
    parser = ArgumentParser(
        prog="certo",
        description="Turn conversations into verifiable specifications.",
    )
    _add_global_args(parser)

    subparsers = parser.add_subparsers(dest="command")

    # init command
    init_parser = subparsers.add_parser("init", help="initialize a new certo spec")
    _add_global_args(init_parser)

    init_parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing spec",
    )
    init_parser.set_defaults(func=cmd_init)

    # status command
    status_parser = subparsers.add_parser("status", help="show spec status")
    _add_global_args(status_parser)
    status_parser.add_argument(
        "id",
        nargs="?",
        help="specific item ID to show (e.g., c-xxx, i-xxx, x-xxx)",
    )
    status_parser.add_argument(
        "--claims",
        action="store_true",
        help="show only claims",
    )

    status_parser.add_argument(
        "--checks",
        action="store_true",
        help="show only checks",
    )
    status_parser.set_defaults(func=cmd_status)

    # claim command (noun-verb pattern with subcommands)
    add_claim_parser(subparsers, _add_global_args)

    # check command (noun-verb pattern with subcommands)
    add_check_parser(subparsers, _add_global_args)

    # scan command
    scan_parser = subparsers.add_parser(
        "scan", help="discover assumptions and check consistency"
    )
    _add_global_args(scan_parser)
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

    return parser


def _get_parser() -> ArgumentParser:
    """Get the cached argument parser."""
    global _PARSER
    if _PARSER is None:
        _PARSER = _build_parser()
    return _PARSER


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    # Normalize argv to move global flags after subcommand
    if argv is None:
        argv = sys.argv[1:]
    argv = _normalize_argv(list(argv))

    parser = _get_parser()

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
