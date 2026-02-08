"""Status command implementation."""

from __future__ import annotations

from argparse import Namespace

from certo.cli.output import Output, get_config_path
from certo.spec import Claim, Spec

# Item type prefixes
ITEM_PREFIXES = [("k-", "check"), ("c-", "claim")]


def _get_item_type(item_id: str) -> str | None:
    """Get item type from ID prefix."""
    for prefix, item_type in ITEM_PREFIXES:
        if item_id.startswith(prefix):
            return item_type
    return None


def cmd_status(args: Namespace, output: Output) -> int:
    """Show spec contents."""
    config_path = get_config_path(args, output)
    if config_path is None:
        return 1

    spec = Spec.load(config_path)
    item_id = getattr(args, "id", None)

    # Show specific item
    if item_id:
        return _show_item(spec, item_id, output)

    # Filter flags
    show_checks = getattr(args, "checks", False)
    show_claims = getattr(args, "claims", False)

    # If no filter, show all
    if not any([show_checks, show_claims]):
        show_checks = show_claims = True

    # Build output data for JSON
    json_data: dict[str, list[dict[str, object]]] = {}

    if show_checks and spec.checks:
        _show_checks(spec, output)
        json_data["checks"] = [
            {
                "id": ch.id,
                "kind": ch.kind,
                "status": ch.status,
            }
            for ch in spec.checks
        ]

    if show_claims and spec.claims:
        if show_checks and spec.checks:
            output.info("")
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
                "created": c.created.isoformat() if c.created else None,
            }
            for c in spec.claims
        ]

    output.json_output(json_data)
    return 0


def _show_item(spec: Spec, item_id: str, output: Output) -> int:
    """Show a specific item by ID."""
    item_type = _get_item_type(item_id)

    match item_type:
        case "check":
            check = spec.get_check(item_id)
            if not check:
                output.error(f"Check not found: {item_id}")
                return 1
            _show_check_detail(check, output)
            output.json_output(
                {
                    "id": check.id,
                    "kind": check.kind,
                    "status": check.status,
                }
            )
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
        case _:
            output.error(f"Unknown item type for ID: {item_id}")
            return 1

    return 0


def _show_checks(spec: Spec, output: Output) -> None:
    """Show checks list."""
    output.info("Checks:")
    for ch in spec.checks:
        status_icon = "●" if ch.status == "enabled" else "○"
        output.info(f"  {status_icon} [{ch.id}] {ch.kind}")


def _show_check_detail(check: object, output: Output) -> None:
    """Show full check details."""
    from certo.probe import LLMConfig, ScanConfig, ShellConfig, UrlConfig

    check_id = getattr(check, "id", "")
    kind = getattr(check, "kind", "")
    status = getattr(check, "status", "enabled")

    output.info(f"ID:     {check_id}")
    output.info(f"Kind:   {kind}")
    output.info(f"Status: {status}")

    match check:
        case UrlConfig():
            output.info(f"URL:    {check.url}")
            if check.cmd:
                output.info(f"Cmd:    {check.cmd}")
        case ShellConfig():
            output.info(f"Cmd:    {check.cmd}")
            if check.exit_code != 0:
                output.info(f"Exit:   {check.exit_code}")
            if check.matches:
                output.info(f"Match:  {check.matches}")
        case LLMConfig():
            output.info(f"Files:  {check.files}")
            if check.prompt:
                output.info(f"Prompt: {check.prompt}")
        case ScanConfig():
            if check.has:
                output.info(f"Has:    {check.has}")
            if check.equals:
                output.info(f"Equals: {check.equals} = {check.value}")
            if check.matches:
                output.info(f"Match:  {check.matches} ~ {check.pattern}")


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
    if claim.verify:
        output.info(f"Verify: {claim.verify.rules}")
    if claim.why:
        output.info("")
        output.info(f"Why: {claim.why}")
    if claim.considered:
        output.info("")
        output.info("Considered:")
        for alt in claim.considered:
            output.info(f"  - {alt}")
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
