"""Command-line interface for certo."""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Any

from certo.check import CheckResult, check_blueprint


class OutputFormat(Enum):
    """Output format options."""

    TEXT = "text"
    JSON = "json"


class Output:
    """Handle output based on verbosity and format settings."""

    def __init__(
        self, *, quiet: bool = False, verbose: bool = False, fmt: OutputFormat
    ) -> None:
        self.quiet = quiet
        self.verbose = verbose
        self.format = fmt
        self._json_data: dict[str, Any] = {}

    def info(self, message: str) -> None:
        """Print info message (normal and verbose mode only)."""
        if not self.quiet and self.format == OutputFormat.TEXT:
            print(message)

    def verbose_info(self, message: str) -> None:
        """Print verbose message (verbose mode only)."""
        if self.verbose and self.format == OutputFormat.TEXT:
            print(message)

    def error(self, message: str) -> None:
        """Print error message (always in text mode, collected for JSON)."""
        if self.format == OutputFormat.TEXT:
            print(message, file=sys.stderr)

    def result(self, result: CheckResult) -> None:
        """Output a single check result."""
        if self.format == OutputFormat.TEXT:
            status = "✓" if result.passed else "✗"
            if result.passed:
                if not self.quiet:
                    print(f"{status} [{result.concern_id}] {result.claim}")
                    if self.verbose:
                        print(f"    Strategy: {result.strategy}")
                        print(f"    {result.message}")
            else:
                # Always show failures
                print(f"{status} [{result.concern_id}] {result.claim}")
                print(f"    {result.message}")

    def summary(self, passed: int, failed: int) -> None:
        """Output summary."""
        if self.format == OutputFormat.TEXT:
            if not self.quiet or failed > 0:
                print()
                print(f"Passed: {passed}, Failed: {failed}")

    def json_output(self, data: dict[str, Any]) -> None:
        """Set JSON output data."""
        self._json_data = data

    def finalize(self) -> None:
        """Finalize output (print JSON if in JSON mode)."""
        if self.format == OutputFormat.JSON:
            print(json.dumps(self._json_data, default=str))


def cmd_check(args: Namespace, output: Output) -> int:
    """Run verification checks against the blueprint."""
    blueprint_path = args.path / ".certo" / "blueprint.toml"

    output.verbose_info(f"Checking blueprint: {blueprint_path}")

    results = check_blueprint(blueprint_path)

    # Display results
    passed = 0
    failed = 0
    for result in results:
        output.result(result)
        if result.passed:
            passed += 1
        else:
            failed += 1

    output.summary(passed, failed)

    # JSON output
    output.json_output(
        {
            "passed": passed,
            "failed": failed,
            "results": [asdict(r) for r in results],
        }
    )

    return 1 if failed > 0 else 0


def cmd_version(args: Namespace, output: Output) -> int:  # noqa: ARG001
    """Print version information."""
    from certo import __version__

    if output.format == OutputFormat.JSON:
        output.json_output({"version": __version__})
    else:
        print(f"certo {__version__}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = ArgumentParser(
        prog="certo",
        description="Turn conversations into verifiable specifications.",
    )
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

    subparsers = parser.add_subparsers(dest="command")

    # check command
    check_parser = subparsers.add_parser("check", help="verify blueprint against code")
    check_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="project root (default: current directory)",
    )
    check_parser.set_defaults(func=cmd_check)

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
