"""Claim command implementation."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace, _SubParsersAction
from typing import Callable

from certo.cli.output import Output
from certo.spec import Claim, Spec, generate_id, now_utc


def add_claim_parser(
    subparsers: _SubParsersAction[ArgumentParser],
    add_global_args: Callable[[ArgumentParser], None],
) -> None:
    """Add claim subcommand and its subparsers."""
    claim_parser = subparsers.add_parser("claim", help="manage claims")
    add_global_args(claim_parser)
    claim_subparsers = claim_parser.add_subparsers(dest="claim_command")

    # claim add
    add_parser = claim_subparsers.add_parser("add", help="create a new claim")
    add_global_args(add_parser)
    add_parser.add_argument("text", help="claim text")
    add_parser.add_argument(
        "--level", choices=["block", "warn", "skip"], default="warn"
    )
    add_parser.add_argument("--tags", help="comma-separated tags")
    add_parser.add_argument("--why", help="rationale for the claim")
    add_parser.add_argument("--closes", help="comma-separated issue IDs to close")
    add_parser.add_argument("--author", help="author name")
    add_parser.set_defaults(func=cmd_claim_add)

    # claim list
    list_parser = claim_subparsers.add_parser("list", help="list claims")
    add_global_args(list_parser)
    list_parser.add_argument(
        "--status",
        choices=["pending", "confirmed", "rejected", "superseded"],
        help="filter by status",
    )
    list_parser.set_defaults(func=cmd_claim_list)

    # claim view
    view_parser = claim_subparsers.add_parser("view", help="view a claim")
    add_global_args(view_parser)
    view_parser.add_argument("id", help="claim ID")
    view_parser.set_defaults(func=cmd_claim_view)

    # claim confirm
    confirm_parser = claim_subparsers.add_parser("confirm", help="confirm a claim")
    add_global_args(confirm_parser)
    confirm_parser.add_argument("id", help="claim ID")
    confirm_parser.set_defaults(func=cmd_claim_confirm)

    # claim reject
    reject_parser = claim_subparsers.add_parser("reject", help="reject a claim")
    add_global_args(reject_parser)
    reject_parser.add_argument("id", help="claim ID")
    reject_parser.add_argument("--reason", help="reason for rejection")
    reject_parser.set_defaults(func=cmd_claim_reject)

    # Default: show help
    def cmd_claim_help(args: Namespace, output: Output) -> int:  # noqa: ARG001
        claim_parser.print_help()
        return 0

    claim_parser.set_defaults(func=cmd_claim_help)


def cmd_claim_add(args: Namespace, output: Output) -> int:
    """Create a new claim."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)

    text = args.text
    claim_id = generate_id("c", text)

    if spec.get_claim(claim_id):
        output.error(f"Claim already exists: {claim_id}")
        return 1

    claim = Claim(
        id=claim_id,
        text=text,
        status="pending",
        source="human",
        author=getattr(args, "author", "") or "",
        level=getattr(args, "level", "warn") or "warn",
        tags=_parse_list(getattr(args, "tags", None)),
        created=now_utc(),
        why=getattr(args, "why", "") or "",
        closes=_parse_list(getattr(args, "closes", None)),
    )

    spec.claims.append(claim)
    spec.save(spec_path)

    output.success(f"Created claim: {claim_id}")
    output.json_output({"id": claim_id, "text": text})

    return 0


def cmd_claim_list(args: Namespace, output: Output) -> int:
    """List claims."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    status_filter = getattr(args, "status", None)

    claims = spec.claims
    if status_filter:
        claims = [c for c in claims if c.status == status_filter]

    if not claims:
        output.info("No claims found")
        output.json_output({"claims": []})
        return 0

    for claim in claims:
        _print_claim_summary(claim, output)

    output.json_output(
        {
            "claims": [
                {"id": c.id, "text": c.text, "status": c.status, "level": c.level}
                for c in claims
            ]
        }
    )

    return 0


def cmd_claim_view(args: Namespace, output: Output) -> int:
    """View a specific claim."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    claim = spec.get_claim(args.id)

    if not claim:
        output.error(f"Claim not found: {args.id}")
        return 1

    _print_claim_detail(claim, output)
    output.json_output(
        {
            "id": claim.id,
            "text": claim.text,
            "status": claim.status,
            "level": claim.level,
            "source": claim.source,
            "author": claim.author,
            "tags": claim.tags,
            "created": claim.created,
            "updated": claim.updated,
            "why": claim.why,
            "closes": claim.closes,
            "checks": len(claim.checks),
        }
    )

    return 0


def cmd_claim_confirm(args: Namespace, output: Output) -> int:
    """Confirm a pending claim."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    claim = spec.get_claim(args.id)

    if not claim:
        output.error(f"Claim not found: {args.id}")
        return 1

    if claim.status == "confirmed":
        output.info(f"Claim already confirmed: {args.id}")
        return 0

    claim.status = "confirmed"
    claim.updated = now_utc()
    spec.save(spec_path)

    output.success(f"Confirmed: {args.id}")
    output.json_output({"id": args.id, "status": "confirmed"})

    return 0


def cmd_claim_reject(args: Namespace, output: Output) -> int:
    """Reject a claim."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    claim = spec.get_claim(args.id)

    if not claim:
        output.error(f"Claim not found: {args.id}")
        return 1

    if claim.status == "rejected":
        output.info(f"Claim already rejected: {args.id}")
        return 0

    claim.status = "rejected"
    claim.updated = now_utc()
    spec.save(spec_path)

    output.success(f"Rejected: {args.id}")
    output.json_output({"id": args.id, "status": "rejected"})

    return 0


def _print_claim_summary(claim: Claim, output: Output) -> None:
    """Print a one-line claim summary."""
    if output.quiet:
        return
    status_icon = {
        "pending": "○",
        "confirmed": "✓",
        "rejected": "✗",
        "superseded": "→",
    }.get(claim.status, "?")
    print(f"{status_icon} [{claim.id}] {claim.text}")


def _print_claim_detail(claim: Claim, output: Output) -> None:
    """Print detailed claim info."""
    if output.quiet:
        return
    print(f"ID:      {claim.id}")
    print(f"Text:    {claim.text}")
    print(f"Status:  {claim.status}")
    print(f"Level:   {claim.level}")
    if claim.author:
        print(f"Author:  {claim.author}")
    if claim.tags:
        print(f"Tags:    {', '.join(claim.tags)}")
    if claim.why:
        print(f"Why:     {claim.why}")
    if claim.checks:
        print(f"Checks:  {len(claim.checks)}")
    print(f"Created: {claim.created}")
    if claim.updated:
        print(f"Updated: {claim.updated}")


def _parse_list(value: str | None) -> list[str]:
    """Parse comma-separated values."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]
