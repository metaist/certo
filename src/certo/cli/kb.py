"""Knowledge base command implementation."""

from __future__ import annotations

from argparse import Namespace

from certo.cli.output import Output


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
