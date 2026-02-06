"""Context command implementation."""

from __future__ import annotations

from argparse import Namespace

from certo.cli.output import Output
from certo.spec import Context, Spec, generate_id, now_utc


def cmd_context(args: Namespace, output: Output) -> int:
    """Create a new context."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    name = getattr(args, "name", None)

    if not name:
        output.error("Context name is required")
        return 1

    # Generate ID from name
    context_id = generate_id("x", name)

    # Check for duplicate
    if spec.get_context(context_id):
        output.error(f"Context already exists: {context_id}")
        return 1

    # Create context
    context = Context(
        id=context_id,
        name=name,
        description=getattr(args, "description", "") or "",
        created=now_utc(),
    )

    spec.contexts.append(context)
    spec.save(spec_path)

    output.info(f"Created context: {context_id}")
    output.json_output({"id": context_id, "name": name})

    return 0
