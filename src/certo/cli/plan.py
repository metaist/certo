"""Plan command implementation."""

from __future__ import annotations

from argparse import Namespace

from certo.blueprint import Blueprint, Concern, Context, Decision
from certo.cli.output import Output

# Item type prefixes (order matters - longer prefixes first)
ITEM_PREFIXES = [("ctx", "context"), ("d", "decision"), ("c", "concern")]


def _get_item_type(item_id: str) -> str | None:
    """Get item type from ID prefix."""
    for prefix, item_type in ITEM_PREFIXES:
        if item_id.startswith(prefix):
            return item_type
    return None


def cmd_plan_show(args: Namespace, output: Output) -> int:
    """Show blueprint contents."""
    blueprint_path = args.path / ".certo" / "blueprint.toml"

    if not blueprint_path.exists():
        output.error(f"No blueprint found at {blueprint_path}")
        return 1

    blueprint = Blueprint.load(blueprint_path)
    item_id = getattr(args, "id", None)

    # Show specific item
    if item_id:
        return _show_item(blueprint, item_id, output)

    # Filter flags
    show_decisions = getattr(args, "decisions", False)
    show_concerns = getattr(args, "concerns", False)
    show_contexts = getattr(args, "contexts", False)

    # If no filter, show all
    if not any([show_decisions, show_concerns, show_contexts]):
        show_decisions = show_concerns = show_contexts = True

    # Build output data for JSON
    json_data: dict[str, list[dict[str, object]]] = {}

    if show_decisions and blueprint.decisions:
        _show_decisions(blueprint, output)
        json_data["decisions"] = [
            {
                "id": d.id,
                "title": d.title,
                "status": d.status,
                "description": d.description,
                "rationale": d.rationale,
                "alternatives": d.alternatives,
                "decided_by": d.decided_by,
                "decided_on": d.decided_on.isoformat() if d.decided_on else None,
            }
            for d in blueprint.decisions
        ]

    if show_concerns and blueprint.concerns:
        if show_decisions and blueprint.decisions:
            output.info("")
        _show_concerns(blueprint, output)
        json_data["concerns"] = [
            {
                "id": c.id,
                "claim": c.claim,
                "category": c.category,
                "strategy": c.strategy,
                "failure": c.failure,
                "traces_to": c.traces_to,
            }
            for c in blueprint.concerns
        ]

    if show_contexts and blueprint.contexts:
        if (show_decisions and blueprint.decisions) or (
            show_concerns and blueprint.concerns
        ):
            output.info("")
        _show_contexts(blueprint, output)
        json_data["contexts"] = [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "applies_to": c.applies_to,
                "expires": c.expires.isoformat() if c.expires else None,
            }
            for c in blueprint.contexts
        ]

    output.json_output(json_data)
    return 0


def _show_item(blueprint: Blueprint, item_id: str, output: Output) -> int:
    """Show a specific item by ID."""
    item_type = _get_item_type(item_id)

    if item_type == "decision":
        decision = blueprint.get_decision(item_id)
        if not decision:
            output.error(f"Decision not found: {item_id}")
            return 1
        _show_decision_detail(decision, output)
        output.json_output(
            {
                "id": decision.id,
                "title": decision.title,
                "status": decision.status,
                "description": decision.description,
                "rationale": decision.rationale,
                "alternatives": decision.alternatives,
                "decided_by": decision.decided_by,
                "decided_on": decision.decided_on.isoformat()
                if decision.decided_on
                else None,
            }
        )
    elif item_type == "concern":
        concern = blueprint.get_concern(item_id)
        if not concern:
            output.error(f"Concern not found: {item_id}")
            return 1
        _show_concern_detail(concern, output)
        output.json_output(
            {
                "id": concern.id,
                "claim": concern.claim,
                "category": concern.category,
                "strategy": concern.strategy,
                "context": concern.context,
                "verify_with": concern.verify_with,
                "conditions": concern.conditions,
                "failure": concern.failure,
                "traces_to": concern.traces_to,
            }
        )
    elif item_type == "context":
        context = blueprint.get_context(item_id)
        if not context:
            output.error(f"Context not found: {item_id}")
            return 1
        _show_context_detail(context, output)
        output.json_output(
            {
                "id": context.id,
                "name": context.name,
                "description": context.description,
                "applies_to": context.applies_to,
                "expires": context.expires.isoformat() if context.expires else None,
                "overrides": context.overrides,
            }
        )
    else:
        output.error(f"Unknown item type for ID: {item_id}")
        return 1

    return 0


def _show_decisions(blueprint: Blueprint, output: Output) -> None:
    """Show decisions list."""
    output.info("Decisions:")
    for d in blueprint.decisions:
        status_marker = ""
        if d.status == "superseded":
            status_marker = " [superseded]"
        elif d.status == "deferred":
            status_marker = " [deferred]"
        elif d.status == "proposed":
            status_marker = " [proposed]"

        output.info(f"  {d.id}  {d.title}{status_marker}")

        if output.verbose:
            if d.description:
                # Show first line of description
                first_line = d.description.strip().split("\n")[0]
                if len(first_line) > 60:
                    first_line = first_line[:57] + "..."
                output.info(f"        {first_line}")
            if d.decided_by:
                date_str = d.decided_on.strftime("%Y-%m-%d") if d.decided_on else ""
                output.info(f"        Decided by {d.decided_by} {date_str}".rstrip())


def _show_decision_detail(decision: Decision, output: Output) -> None:
    """Show full decision details."""
    output.info(f"{decision.id}: {decision.title}")
    output.info(f"Status: {decision.status}")
    if decision.description:
        output.info("")
        output.info(decision.description.strip())
    if decision.alternatives:
        output.info("")
        output.info("Alternatives considered:")
        for alt in decision.alternatives:
            output.info(f"  - {alt}")
    if decision.rationale:
        output.info("")
        output.info(f"Rationale: {decision.rationale}")
    if decision.decided_by:
        date_str = (
            decision.decided_on.strftime("%Y-%m-%d") if decision.decided_on else ""
        )
        output.info("")
        output.info(f"Decided by {decision.decided_by} on {date_str}".rstrip())


def _show_concerns(blueprint: Blueprint, output: Output) -> None:
    """Show concerns list."""
    output.info("Concerns:")
    for c in blueprint.concerns:
        category = f"[{c.category}] " if c.category else ""
        output.info(f"  {c.id}  {category}{c.claim}")

        if output.verbose:
            output.info(f"        Strategy: {c.strategy}, Failure: {c.failure}")
            if c.traces_to:
                output.info(f"        Traces to: {', '.join(c.traces_to)}")


def _show_concern_detail(concern: Concern, output: Output) -> None:
    """Show full concern details."""
    output.info(f"{concern.id}: {concern.claim}")
    if concern.category:
        output.info(f"Category: {concern.category}")
    output.info(f"Strategy: {concern.strategy}")
    output.info(f"Failure: {concern.failure}")
    if concern.conditions:
        output.info("")
        output.info("Conditions:")
        for cond in concern.conditions:
            output.info(f"  - {cond}")
    if concern.context:
        output.info("")
        output.info("Context files:")
        for ctx in concern.context:
            output.info(f"  - {ctx}")
    if concern.verify_with:
        output.info("")
        output.info(f"Verify with: {', '.join(concern.verify_with)}")
    if concern.traces_to:
        output.info("")
        output.info(f"Traces to: {', '.join(concern.traces_to)}")


def _show_contexts(blueprint: Blueprint, output: Output) -> None:
    """Show contexts list."""
    output.info("Contexts:")
    for c in blueprint.contexts:
        output.info(f"  {c.id}  {c.name}")

        if output.verbose:
            if c.description:
                first_line = c.description.strip().split("\n")[0]
                if len(first_line) > 60:
                    first_line = first_line[:57] + "..."
                output.info(f"        {first_line}")
            if c.expires:
                output.info(f"        Expires: {c.expires.strftime('%Y-%m-%d')}")


def _show_context_detail(context: Context, output: Output) -> None:
    """Show full context details."""
    output.info(f"{context.id}: {context.name}")
    if context.description:
        output.info("")
        output.info(context.description.strip())
    if context.applies_to:
        output.info("")
        output.info("Applies to:")
        for item in context.applies_to:
            output.info(f"  - {item}")
    if context.expires:
        output.info("")
        output.info(f"Expires: {context.expires.strftime('%Y-%m-%d')}")
    if context.overrides:
        output.info("")
        output.info("Overrides:")
        for key, value in context.overrides.items():
            output.info(f"  {key}: {value}")
