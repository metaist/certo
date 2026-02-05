"""Command-line interface for certo."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from certo.check import check_blueprint


def cmd_check(args: Namespace) -> int:
    """Run verification checks against the blueprint."""
    blueprint_path = args.path / ".certo" / "blueprint.toml"
    results = check_blueprint(blueprint_path)

    # Display results
    passed = 0
    failed = 0
    for result in results:
        status = "✓" if result.passed else "✗"
        print(f"{status} [{result.concern_id}] {result.claim}")
        if not result.passed:
            print(f"  {result.message}")
            failed += 1
        else:
            passed += 1

    # Summary
    print()
    print(f"Passed: {passed}, Failed: {failed}")

    return 1 if failed > 0 else 0


def cmd_version(args: Namespace) -> int:  # noqa: ARG001
    """Print version information."""
    from certo import __version__

    print(f"certo {__version__}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = ArgumentParser(
        prog="certo",
        description="Turn conversations into verifiable specifications.",
    )
    parser.add_argument("--version", action="store_true", help="print version and exit")
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

    if args.version:
        return cmd_version(args)

    if args.command is None:
        parser.print_help()
        return 0

    result: int = args.func(args)
    return result


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
