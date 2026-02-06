"""Scan command implementation."""

from __future__ import annotations

from argparse import Namespace

from certo.cli.output import Output, OutputFormat
from certo.scan import scan_project


def cmd_scan(args: Namespace, output: Output) -> int:
    """Scan project for facts."""
    output.verbose_info(f"Scanning project: {args.path}")

    result = scan_project(args.path)

    # Display facts (text mode only)
    if output.format == OutputFormat.TEXT:
        if result.facts:
            if not output.quiet:
                print("Discovered facts:")
            for fact in result.facts:
                if not output.quiet:
                    print(f"  {fact.key} = {fact.value}")
                    if output.verbose:
                        print(f"    source: {fact.source}")

        # Display errors
        if result.errors:  # pragma: no cover
            for error in result.errors:
                output.error(f"Scan error: {error}")

        # Summary
        if not output.quiet:
            print()
            print(f"Facts: {len(result.facts)}, Errors: {len(result.errors)}")

    # JSON output
    output.json_output(
        {
            "facts": [
                {
                    "key": f.key,
                    "value": f.value,
                    "source": f.source,
                    "confidence": f.confidence,
                }
                for f in result.facts
            ],
            "errors": result.errors,
        }
    )

    return 1 if result.errors else 0
