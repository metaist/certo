"""Context command implementation."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace, _SubParsersAction
from typing import Callable

from certo.cli.output import Output
from certo.spec import Context, Spec, generate_id, now_utc


def add_context_parser(
    subparsers: _SubParsersAction[ArgumentParser],
    add_global_args: Callable[[ArgumentParser], None],
) -> None:
    """Add context subcommand and its subparsers."""
    ctx_parser = subparsers.add_parser("context", help="manage contexts")
    add_global_args(ctx_parser)
    ctx_subparsers = ctx_parser.add_subparsers(dest="context_command")

    # context add
    add_parser = ctx_subparsers.add_parser("add", help="create a new context")
    add_global_args(add_parser)
    add_parser.add_argument("name", help="context name")
    add_parser.add_argument("--description", help="context description")
    add_parser.set_defaults(func=cmd_context_add)

    # context list
    list_parser = ctx_subparsers.add_parser("list", help="list contexts")
    add_global_args(list_parser)
    list_parser.add_argument(
        "--status",
        choices=["enabled", "disabled"],
        help="filter by status",
    )
    list_parser.set_defaults(func=cmd_context_list)

    # context view
    view_parser = ctx_subparsers.add_parser("view", help="view a context")
    add_global_args(view_parser)
    view_parser.add_argument("id", help="context ID")
    view_parser.set_defaults(func=cmd_context_view)

    # context on (enable)
    on_parser = ctx_subparsers.add_parser("on", help="enable a context")
    add_global_args(on_parser)
    on_parser.add_argument("id", help="context ID")
    on_parser.set_defaults(func=cmd_context_on)

    # context off (disable)
    off_parser = ctx_subparsers.add_parser("off", help="disable a context")
    add_global_args(off_parser)
    off_parser.add_argument("id", help="context ID")
    off_parser.set_defaults(func=cmd_context_off)

    # Default: show help
    def cmd_context_help(args: Namespace, output: Output) -> int:  # noqa: ARG001
        ctx_parser.print_help()
        return 0

    ctx_parser.set_defaults(func=cmd_context_help)


def cmd_context_add(args: Namespace, output: Output) -> int:
    """Create a new context."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)

    name = args.name
    context_id = generate_id("x", name)

    if spec.get_context(context_id):
        output.error(f"Context already exists: {context_id}")
        return 1

    context = Context(
        id=context_id,
        name=name,
        description=getattr(args, "description", "") or "",
        created=now_utc(),
    )

    spec.contexts.append(context)
    spec.save(spec_path)

    output.success(f"Created context: {context_id}")
    output.json_output({"id": context_id, "name": name})

    return 0


def cmd_context_list(args: Namespace, output: Output) -> int:
    """List contexts."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    status_filter = getattr(args, "status", None)

    contexts = spec.contexts
    if status_filter:
        if status_filter == "enabled":
            contexts = [c for c in contexts if c.enabled]
        else:
            contexts = [c for c in contexts if not c.enabled]

    if not contexts:
        output.info("No contexts found")
        output.json_output({"contexts": []})
        return 0

    for context in contexts:
        _print_context_summary(context, output)

    output.json_output(
        {
            "contexts": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "enabled": c.enabled,
                }
                for c in contexts
            ]
        }
    )

    return 0


def cmd_context_view(args: Namespace, output: Output) -> int:
    """View a specific context."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    context = spec.get_context(args.id)

    if not context:
        output.error(f"Context not found: {args.id}")
        return 1

    _print_context_detail(context, output)
    output.json_output(
        {
            "id": context.id,
            "name": context.name,
            "description": context.description,
            "enabled": context.enabled,
            "created": context.created,
            "updated": context.updated,
        }
    )

    return 0


def cmd_context_on(args: Namespace, output: Output) -> int:
    """Enable a context."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    context = spec.get_context(args.id)

    if not context:
        output.error(f"Context not found: {args.id}")
        return 1

    if context.enabled:
        output.info(f"Context already enabled: {args.id}")
        return 0

    context.enabled = True
    context.updated = now_utc()
    spec.save(spec_path)

    output.success(f"Enabled: {args.id}")
    output.json_output({"id": args.id, "enabled": True})

    return 0


def cmd_context_off(args: Namespace, output: Output) -> int:
    """Disable a context."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    context = spec.get_context(args.id)

    if not context:
        output.error(f"Context not found: {args.id}")
        return 1

    if not context.enabled:
        output.info(f"Context already disabled: {args.id}")
        return 0

    context.enabled = False
    context.updated = now_utc()
    spec.save(spec_path)

    output.success(f"Disabled: {args.id}")
    output.json_output({"id": args.id, "enabled": False})

    return 0


def _print_context_summary(context: Context, output: Output) -> None:
    """Print a one-line context summary."""
    if output.quiet:
        return
    status_icon = "●" if context.enabled else "○"
    print(f"{status_icon} [{context.id}] {context.name}")


def _print_context_detail(context: Context, output: Output) -> None:
    """Print detailed context info."""
    if output.quiet:
        return
    print(f"ID:          {context.id}")
    print(f"Name:        {context.name}")
    print(f"Description: {context.description or '(none)'}")
    print(f"Enabled:     {context.enabled}")
    print(f"Created:     {context.created}")
    if context.updated:
        print(f"Updated:     {context.updated}")
