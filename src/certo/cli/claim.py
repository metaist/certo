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

    # claim check (nested subcommand)
    check_parser = claim_subparsers.add_parser("check", help="manage checks on a claim")
    add_global_args(check_parser)
    check_subparsers = check_parser.add_subparsers(dest="check_command")

    # claim check add
    check_add_parser = check_subparsers.add_parser("add", help="add a check to a claim")
    add_global_args(check_add_parser)
    check_add_parser.add_argument("claim_id", help="claim ID")
    check_add_parser.add_argument(
        "kind", choices=["shell", "llm", "fact", "url"], help="check kind"
    )
    check_add_parser.add_argument("--cmd", help="shell command (for shell checks)")
    check_add_parser.add_argument(
        "--exit-code", type=int, default=0, help="expected exit code (for shell checks)"
    )
    check_add_parser.add_argument(
        "--matches", help="comma-separated patterns that must match (for shell checks)"
    )
    check_add_parser.add_argument(
        "--not-matches",
        help="comma-separated patterns that must not match (for shell checks)",
    )
    check_add_parser.add_argument(
        "--timeout", type=int, default=60, help="timeout in seconds (for shell checks)"
    )
    check_add_parser.add_argument(
        "--files", help="comma-separated file patterns (for llm checks)"
    )
    check_add_parser.add_argument("--prompt", help="custom prompt (for llm checks)")
    check_add_parser.add_argument(
        "--has", help="fact key that must exist (for fact checks)"
    )
    check_add_parser.add_argument(
        "--empty", help="fact key that must be empty (for fact checks)"
    )
    check_add_parser.add_argument(
        "--equals", help="fact key that must equal --value (for fact checks)"
    )
    check_add_parser.add_argument("--value", help="value to compare (for fact checks)")
    check_add_parser.add_argument(
        "--fact-matches", help="fact key that must match --pattern (for fact checks)"
    )
    check_add_parser.add_argument(
        "--pattern", help="regex pattern to match (for fact checks)"
    )
    check_add_parser.add_argument("--url", help="URL to fetch (for url checks)")
    check_add_parser.add_argument(
        "--cache-ttl",
        type=int,
        default=86400,
        help="cache duration in seconds (for url checks, default: 86400)",
    )
    check_add_parser.set_defaults(func=cmd_claim_check_add)

    # claim check list
    check_list_parser = check_subparsers.add_parser(
        "list", help="list checks on a claim"
    )
    add_global_args(check_list_parser)
    check_list_parser.add_argument("claim_id", help="claim ID")
    check_list_parser.set_defaults(func=cmd_claim_check_list)

    # claim check view
    check_view_parser = check_subparsers.add_parser("view", help="view a check")
    add_global_args(check_view_parser)
    check_view_parser.add_argument("check_id", help="check ID")
    check_view_parser.set_defaults(func=cmd_claim_check_view)

    # claim check on
    check_on_parser = check_subparsers.add_parser("on", help="enable a check")
    add_global_args(check_on_parser)
    check_on_parser.add_argument("check_id", help="check ID")
    check_on_parser.set_defaults(func=cmd_claim_check_on)

    # claim check off
    check_off_parser = check_subparsers.add_parser("off", help="disable a check")
    add_global_args(check_off_parser)
    check_off_parser.add_argument("check_id", help="check ID")
    check_off_parser.set_defaults(func=cmd_claim_check_off)

    # Default for claim check: show help
    def cmd_check_help(args: Namespace, output: Output) -> int:  # noqa: ARG001
        check_parser.print_help()
        return 0

    check_parser.set_defaults(func=cmd_check_help)

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
    else:
        # Hide rejected claims by default
        claims = [c for c in claims if c.status != "rejected"]

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
        "rejected": "⊘",  # Different from failure ✗
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


def cmd_claim_check_add(args: Namespace, output: Output) -> int:
    """Add a check to a claim."""
    from certo.check import FactCheck, LLMCheck, ShellCheck, UrlCheck

    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    claim = spec.get_claim(args.claim_id)

    if not claim:
        output.error(f"Claim not found: {args.claim_id}")
        return 1

    check: ShellCheck | LLMCheck | FactCheck | UrlCheck

    match args.kind:
        case "shell":
            if not args.cmd:
                output.error("--cmd is required for shell checks")
                return 1
            shell_check = ShellCheck(
                cmd=args.cmd,
                exit_code=args.exit_code,
                matches=_parse_list(args.matches),
                not_matches=_parse_list(args.not_matches),
                timeout=args.timeout,
            )
            shell_check.id = generate_id("k", f"shell:{shell_check.cmd}")
            check = shell_check

        case "llm":
            if not args.files:
                output.error("--files is required for llm checks")
                return 1
            llm_check = LLMCheck(
                files=_parse_list(args.files),
                prompt=args.prompt,
            )
            llm_check.id = generate_id("k", f"llm:{','.join(llm_check.files)}")
            check = llm_check

        case "fact":
            if (
                not args.has
                and not args.empty
                and not args.equals
                and not args.fact_matches
            ):
                output.error(
                    "--has, --empty, --equals, or --fact-matches is required for fact checks"
                )
                return 1
            empty_val = getattr(args, "empty", "") or ""
            fact_check = FactCheck(
                has=args.has or "",
                empty=empty_val,
                equals=args.equals or "",
                value=args.value or "",
                matches=args.fact_matches or "",
                pattern=args.pattern or "",
            )
            content = f"fact:{fact_check.has}{fact_check.empty}{fact_check.equals}{fact_check.matches}"
            fact_check.id = generate_id("k", content)
            check = fact_check

        case "url":
            if not args.url:
                output.error("--url is required for url checks")
                return 1
            url_check = UrlCheck(
                url=args.url,
                cache_ttl=args.cache_ttl,
                cmd=args.cmd or "",
                exit_code=args.exit_code,
                matches=_parse_list(args.matches),
                not_matches=_parse_list(args.not_matches),
                timeout=args.timeout,
            )
            url_check.id = generate_id("k", f"url:{url_check.url}")
            check = url_check

        case _:
            output.error(f"Unknown check kind: {args.kind}")
            return 1

    claim.checks.append(check)
    claim.updated = now_utc()
    spec.save(spec_path)

    output.success(f"Added check: {check.id}")
    output.json_output({"id": check.id, "kind": args.kind, "claim_id": args.claim_id})

    return 0


def cmd_claim_check_list(args: Namespace, output: Output) -> int:
    """List checks on a claim."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    claim = spec.get_claim(args.claim_id)

    if not claim:
        output.error(f"Claim not found: {args.claim_id}")
        return 1

    if not claim.checks:
        output.info("No checks defined")
        output.json_output({"checks": []})
        return 0

    for check in claim.checks:
        _print_check_summary(check, output)

    output.json_output(
        {
            "checks": [
                {"id": c.id, "kind": c.kind, "status": c.status} for c in claim.checks
            ]
        }
    )

    return 0


def cmd_claim_check_view(args: Namespace, output: Output) -> int:
    """View a specific check."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    result = spec.get_check(args.check_id)

    if not result:
        output.error(f"Check not found: {args.check_id}")
        return 1

    claim, check = result
    _print_check_detail(claim, check, output)

    return 0


def cmd_claim_check_on(args: Namespace, output: Output) -> int:
    """Enable a check."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    result = spec.get_check(args.check_id)

    if not result:
        output.error(f"Check not found: {args.check_id}")
        return 1

    claim, check = result

    if check.status == "enabled":
        output.info(f"Check already enabled: {args.check_id}")
        return 0

    check.status = "enabled"
    claim.updated = now_utc()
    spec.save(spec_path)

    output.success(f"Enabled: {args.check_id}")
    output.json_output({"id": args.check_id, "status": "enabled"})

    return 0


def cmd_claim_check_off(args: Namespace, output: Output) -> int:
    """Disable a check."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)
    result = spec.get_check(args.check_id)

    if not result:
        output.error(f"Check not found: {args.check_id}")
        return 1

    claim, check = result

    if check.status == "disabled":
        output.info(f"Check already disabled: {args.check_id}")
        return 0

    check.status = "disabled"
    claim.updated = now_utc()
    spec.save(spec_path)

    output.success(f"Disabled: {args.check_id}")
    output.json_output({"id": args.check_id, "status": "disabled"})

    return 0


def _print_check_summary(check: object, output: Output) -> None:
    """Print a one-line check summary."""
    if output.quiet:
        return
    status_icon = "●" if getattr(check, "status", "enabled") == "enabled" else "○"
    kind = getattr(check, "kind", "?")
    check_id = getattr(check, "id", "?")
    print(f"{status_icon} [{check_id}] {kind}")


def _print_check_detail(claim: Claim, check: object, output: Output) -> None:
    """Print detailed check info."""
    if output.quiet:
        return

    from certo.check import FactCheck, LLMCheck, ShellCheck, UrlCheck

    check_id = getattr(check, "id", "")
    kind = getattr(check, "kind", "")
    status = getattr(check, "status", "enabled")

    print(f"ID:      {check_id}")
    print(f"Kind:    {kind}")
    print(f"Status:  {status}")
    print(f"Claim:   {claim.id}")

    match check:
        case UrlCheck():
            # UrlCheck extends ShellCheck, handle first
            print(f"URL:     {check.url}")
            if check.cache_ttl != 86400:
                print(f"TTL:     {check.cache_ttl}s")
            if check.cmd:
                print(f"Command: {check.cmd}")
            if check.exit_code != 0:
                print(f"Exit:    {check.exit_code}")
            if check.matches:
                print(f"Matches: {check.matches}")
            if check.not_matches:
                print(f"Not:     {check.not_matches}")
            if check.timeout != 60:
                print(f"Timeout: {check.timeout}s")
            output.json_output(
                {
                    "id": check_id,
                    "kind": kind,
                    "status": status,
                    "claim_id": claim.id,
                    "url": check.url,
                    "cache_ttl": check.cache_ttl,
                    "cmd": check.cmd,
                    "exit_code": check.exit_code,
                    "matches": check.matches,
                    "not_matches": check.not_matches,
                    "timeout": check.timeout,
                }
            )

        case ShellCheck():
            print(f"Command: {check.cmd}")
            if check.exit_code != 0:
                print(f"Exit:    {check.exit_code}")
            if check.matches:
                print(f"Matches: {check.matches}")
            if check.not_matches:
                print(f"Not:     {check.not_matches}")
            if check.timeout != 60:
                print(f"Timeout: {check.timeout}s")
            output.json_output(
                {
                    "id": check_id,
                    "kind": kind,
                    "status": status,
                    "claim_id": claim.id,
                    "cmd": check.cmd,
                    "exit_code": check.exit_code,
                    "matches": check.matches,
                    "not_matches": check.not_matches,
                    "timeout": check.timeout,
                }
            )

        case LLMCheck():
            print(f"Files:   {check.files}")
            if check.prompt:
                print(f"Prompt:  {check.prompt}")
            output.json_output(
                {
                    "id": check_id,
                    "kind": kind,
                    "status": status,
                    "claim_id": claim.id,
                    "files": check.files,
                    "prompt": check.prompt,
                }
            )

        case FactCheck():
            if check.has:
                print(f"Has:     {check.has}")
            if check.equals:
                print(f"Equals:  {check.equals}")
                print(f"Value:   {check.value}")
            if check.matches:
                print(f"Matches: {check.matches}")
                print(f"Pattern: {check.pattern}")
            output.json_output(
                {
                    "id": check_id,
                    "kind": kind,
                    "status": status,
                    "claim_id": claim.id,
                    "has": check.has,
                    "equals": check.equals,
                    "value": check.value,
                    "matches": check.matches,
                    "pattern": check.pattern,
                }
            )
