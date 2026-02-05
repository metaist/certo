"""Scan command implementation."""

from __future__ import annotations

from argparse import Namespace

from certo.cli.output import Output, OutputFormat
from certo.scan import scan_project


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
