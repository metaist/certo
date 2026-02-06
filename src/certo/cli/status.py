"""Status command implementation."""

from __future__ import annotations

from argparse import Namespace

from certo.cli.output import Output
from certo.spec import Claim, Context, Issue, Spec

# Item type prefixes (order matters - longer prefixes first)
ITEM_PREFIXES = [("x-", "context"), ("i-", "issue"), ("c-", "claim")]


def _get_item_type(item_id: str) -> str | None:
    """Get item type from ID prefix."""
    for prefix, item_type in ITEM_PREFIXES:
        if item_id.startswith(prefix):
            return item_type
    return None


def cmd_status(args: Namespace, output: Output) -> int:
    """Show spec contents."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    item_id = getattr(args, "id", None)

    # Show specific item
    if item_id:
        return _show_item(spec, item_id, output)

    # Filter flags
    show_claims = getattr(args, "claims", False)
    show_issues = getattr(args, "issues", False)
    show_contexts = getattr(args, "contexts", False)

    # If no filter, show all
    if not any([show_claims, show_issues, show_contexts]):
        show_claims = show_issues = show_contexts = True

    # Build output data for JSON
    json_data: dict[str, list[dict[str, object]]] = {}

    if show_claims and spec.claims:
        _show_claims(spec, output)
        json_data["claims"] = [
            {
                "id": c.id,
                "text": c.text,
                "status": c.status,
                "source": c.source,
                "author": c.author,
                "level": c.level,
                "tags": c.tags,
                "checks": [{"kind": ch.kind} for ch in c.checks],
                "created": c.created.isoformat() if c.created else None,
            }
            for c in spec.claims
        ]

    if show_issues and spec.issues:
        if show_claims and spec.claims:
            output.info("")
        _show_issues(spec, output)
        json_data["issues"] = [
            {
                "id": i.id,
                "text": i.text,
                "status": i.status,
                "tags": i.tags,
                "created": i.created.isoformat() if i.created else None,
            }
            for i in spec.issues
        ]

    if show_contexts and spec.contexts:
        if (show_claims and spec.claims) or (show_issues and spec.issues):
            output.info("")
        _show_contexts(spec, output)
        json_data["contexts"] = [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "expires": c.expires.isoformat() if c.expires else None,
            }
            for c in spec.contexts
        ]

    output.json_output(json_data)
    return 0


def _show_item(spec: Spec, item_id: str, output: Output) -> int:
    """Show a specific item by ID."""
    item_type = _get_item_type(item_id)

    match item_type:
        case "claim":
            claim = spec.get_claim(item_id)
            if not claim:
                output.error(f"Claim not found: {item_id}")
                return 1
            _show_claim_detail(claim, output)
            output.json_output(
                {
                    "id": claim.id,
                    "text": claim.text,
                    "status": claim.status,
                    "source": claim.source,
                    "author": claim.author,
                    "level": claim.level,
                    "tags": claim.tags,
                    "checks": [{"kind": ch.kind} for ch in claim.checks],
                    "evidence": claim.evidence,
                    "why": claim.why,
                    "considered": claim.considered,
                    "traces_to": claim.traces_to,
                    "supersedes": claim.supersedes,
                    "closes": claim.closes,
                    "created": claim.created.isoformat() if claim.created else None,
                    "updated": claim.updated.isoformat() if claim.updated else None,
                }
            )
        case "issue":
            issue = spec.get_issue(item_id)
            if not issue:
                output.error(f"Issue not found: {item_id}")
                return 1
            _show_issue_detail(issue, output)
            output.json_output(
                {
                    "id": issue.id,
                    "text": issue.text,
                    "status": issue.status,
                    "tags": issue.tags,
                    "closed_reason": issue.closed_reason,
                    "created": issue.created.isoformat() if issue.created else None,
                    "updated": issue.updated.isoformat() if issue.updated else None,
                }
            )
        case "context":
            context = spec.get_context(item_id)
            if not context:
                output.error(f"Context not found: {item_id}")
                return 1
            _show_context_detail(context, output)
            output.json_output(
                {
                    "id": context.id,
                    "name": context.name,
                    "description": context.description,
                    "expires": context.expires.isoformat() if context.expires else None,
                    "modifications": [
                        {
                            "action": m.action,
                            "claim": m.claim,
                            "level": m.level,
                            "topic": m.topic,
                        }
                        for m in context.modifications
                    ],
                    "created": context.created.isoformat() if context.created else None,
                    "updated": context.updated.isoformat() if context.updated else None,
                }
            )
        case _:
            output.error(f"Unknown item type for ID: {item_id}")
            return 1

    return 0


def _show_claims(spec: Spec, output: Output) -> None:
    """Show claims list."""
    output.info("Claims:")
    for c in spec.claims:
        match c.status:
            case "superseded":
                status_marker = " [superseded]"
            case "rejected":
                status_marker = " [rejected]"
            case "pending":
                status_marker = " [pending]"
            case _:
                status_marker = ""

        match c.level:
            case "block":
                level_marker = " *"
            case "skip":
                level_marker = " -"
            case _:
                level_marker = ""

        output.info(f"  {c.id}  {c.text}{status_marker}{level_marker}")

        if output.verbose:
            if c.tags:
                output.info(f"        Tags: {', '.join(c.tags)}")
            if c.author:
                date_str = c.created.strftime("%Y-%m-%d") if c.created else ""
                output.info(f"        By {c.author} {date_str}".rstrip())


def _show_claim_detail(claim: Claim, output: Output) -> None:
    """Show full claim details."""
    output.info(f"{claim.id}: {claim.text}")
    output.info(f"Status: {claim.status}")
    output.info(f"Level: {claim.level}")
    output.info(f"Source: {claim.source}")
    if claim.author:
        output.info(f"Author: {claim.author}")
    if claim.tags:
        output.info(f"Tags: {', '.join(claim.tags)}")
    if claim.why:
        output.info("")
        output.info(f"Why: {claim.why}")
    if claim.considered:
        output.info("")
        output.info("Considered:")
        for alt in claim.considered:
            output.info(f"  - {alt}")
    if claim.checks:
        output.info("")
        output.info("Checks:")
        for check in claim.checks:
            output.info(f"  - {check.kind}")
    if claim.evidence:
        output.info("")
        output.info("Evidence:")
        for e in claim.evidence:
            output.info(f"  - {e}")
    if claim.traces_to:
        output.info("")
        output.info(f"Traces to: {', '.join(claim.traces_to)}")
    if claim.supersedes:
        output.info(f"Supersedes: {claim.supersedes}")
    if claim.closes:
        output.info(f"Closes: {', '.join(claim.closes)}")
    if claim.created:
        output.info("")
        output.info(f"Created: {claim.created.strftime('%Y-%m-%d %H:%M')}")
    if claim.updated:
        output.info(f"Updated: {claim.updated.strftime('%Y-%m-%d %H:%M')}")


def _show_issues(spec: Spec, output: Output) -> None:
    """Show issues list."""
    output.info("Issues:")
    for i in spec.issues:
        status_marker = " [closed]" if i.status == "closed" else ""
        output.info(f"  {i.id}  {i.text}{status_marker}")

        if output.verbose:
            if i.tags:
                output.info(f"        Tags: {', '.join(i.tags)}")
            if i.closed_reason:
                output.info(f"        Reason: {i.closed_reason}")


def _show_issue_detail(issue: Issue, output: Output) -> None:
    """Show full issue details."""
    output.info(f"{issue.id}: {issue.text}")
    output.info(f"Status: {issue.status}")
    if issue.tags:
        output.info(f"Tags: {', '.join(issue.tags)}")
    if issue.closed_reason:
        output.info(f"Closed reason: {issue.closed_reason}")
    if issue.created:
        output.info("")
        output.info(f"Created: {issue.created.strftime('%Y-%m-%d %H:%M')}")
    if issue.updated:
        output.info(f"Updated: {issue.updated.strftime('%Y-%m-%d %H:%M')}")


def _show_contexts(spec: Spec, output: Output) -> None:
    """Show contexts list."""
    output.info("Contexts:")
    for c in spec.contexts:
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
    if context.expires:
        output.info("")
        output.info(f"Expires: {context.expires.strftime('%Y-%m-%d')}")
    if context.modifications:
        output.info("")
        output.info("Modifications:")
        for m in context.modifications:
            match (m.claim, m.level, m.topic):
                case (claim, _, _) if claim:
                    target = claim
                case (_, level, _) if level:
                    target = f"level={level}"
                case (_, _, topic) if topic:
                    target = f"topic={topic}"
                case _:
                    target = "(unknown)"
            output.info(f"  - {target}: {m.action}")
    if context.created:
        output.info("")
        output.info(f"Created: {context.created.strftime('%Y-%m-%d %H:%M')}")
    if context.updated:
        output.info(f"Updated: {context.updated.strftime('%Y-%m-%d %H:%M')}")
