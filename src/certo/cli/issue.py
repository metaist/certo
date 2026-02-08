"""Issue command implementation."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace, _SubParsersAction
from typing import Callable

from certo.cli.output import Output, get_config_path
from certo.spec import Issue, Spec, generate_id, now_utc


def add_issue_parser(
    subparsers: _SubParsersAction[ArgumentParser],
    add_global_args: Callable[[ArgumentParser], None],
) -> None:
    """Add issue subcommand and its subparsers."""
    issue_parser = subparsers.add_parser("issue", help="manage issues")
    add_global_args(issue_parser)
    issue_subparsers = issue_parser.add_subparsers(dest="issue_command")

    # issue add
    add_parser = issue_subparsers.add_parser("add", help="create a new issue")
    add_global_args(add_parser)
    add_parser.add_argument("text", help="issue text")
    add_parser.add_argument("--tags", help="comma-separated tags")
    add_parser.set_defaults(func=cmd_issue_add)

    # issue list
    list_parser = issue_subparsers.add_parser("list", help="list issues")
    add_global_args(list_parser)
    list_parser.add_argument(
        "--status",
        choices=["open", "closed"],
        help="filter by status",
    )
    list_parser.set_defaults(func=cmd_issue_list)

    # issue view
    view_parser = issue_subparsers.add_parser("view", help="view an issue")
    add_global_args(view_parser)
    view_parser.add_argument("id", help="issue ID")
    view_parser.set_defaults(func=cmd_issue_view)

    # issue close
    close_parser = issue_subparsers.add_parser("close", help="close an issue")
    add_global_args(close_parser)
    close_parser.add_argument("id", help="issue ID")
    close_parser.add_argument("--reason", help="reason for closing")
    close_parser.set_defaults(func=cmd_issue_close)

    # issue reopen
    reopen_parser = issue_subparsers.add_parser("reopen", help="reopen an issue")
    add_global_args(reopen_parser)
    reopen_parser.add_argument("id", help="issue ID")
    reopen_parser.set_defaults(func=cmd_issue_reopen)

    # Default: show help
    def cmd_issue_help(args: Namespace, output: Output) -> int:  # noqa: ARG001
        issue_parser.print_help()
        return 0

    issue_parser.set_defaults(func=cmd_issue_help)


def cmd_issue_add(args: Namespace, output: Output) -> int:
    """Create a new issue."""
    config_path = get_config_path(args, output)
    if config_path is None:
        return 1

    spec = Spec.load(config_path)

    text = args.text
    issue_id = generate_id("i", text)

    if spec.get_issue(issue_id):
        output.error(f"Issue already exists: {issue_id}")
        return 1

    issue = Issue(
        id=issue_id,
        text=text,
        status="open",
        tags=_parse_list(getattr(args, "tags", None)),
        created=now_utc(),
    )

    spec.issues.append(issue)
    spec.save(config_path)

    output.success(f"Created issue: {issue_id}")
    output.json_output({"id": issue_id, "text": text})

    return 0


def cmd_issue_list(args: Namespace, output: Output) -> int:
    """List issues."""
    config_path = get_config_path(args, output)
    if config_path is None:
        return 1

    spec = Spec.load(config_path)
    status_filter = getattr(args, "status", None)

    issues = spec.issues
    if status_filter:
        issues = [i for i in issues if i.status == status_filter]

    if not issues:
        output.info("No issues found")
        output.json_output({"issues": []})
        return 0

    for issue in issues:
        _print_issue_summary(issue, output)

    output.json_output(
        {"issues": [{"id": i.id, "text": i.text, "status": i.status} for i in issues]}
    )

    return 0


def cmd_issue_view(args: Namespace, output: Output) -> int:
    """View a specific issue."""
    config_path = get_config_path(args, output)
    if config_path is None:
        return 1

    spec = Spec.load(config_path)
    issue = spec.get_issue(args.id)

    if not issue:
        output.error(f"Issue not found: {args.id}")
        return 1

    _print_issue_detail(issue, output)
    output.json_output(
        {
            "id": issue.id,
            "text": issue.text,
            "status": issue.status,
            "tags": issue.tags,
            "created": issue.created,
            "updated": issue.updated,
            "closed_reason": issue.closed_reason,
        }
    )

    return 0


def cmd_issue_close(args: Namespace, output: Output) -> int:
    """Close an issue."""
    config_path = get_config_path(args, output)
    if config_path is None:
        return 1

    spec = Spec.load(config_path)
    issue = spec.get_issue(args.id)

    if not issue:
        output.error(f"Issue not found: {args.id}")
        return 1

    if issue.status == "closed":
        output.info(f"Issue already closed: {args.id}")
        return 0

    issue.status = "closed"
    issue.updated = now_utc()
    issue.closed_reason = getattr(args, "reason", "") or ""
    spec.save(config_path)

    output.success(f"Closed: {args.id}")
    output.json_output({"id": args.id, "status": "closed"})

    return 0


def cmd_issue_reopen(args: Namespace, output: Output) -> int:
    """Reopen an issue."""
    config_path = get_config_path(args, output)
    if config_path is None:
        return 1

    spec = Spec.load(config_path)
    issue = spec.get_issue(args.id)

    if not issue:
        output.error(f"Issue not found: {args.id}")
        return 1

    if issue.status == "open":
        output.info(f"Issue already open: {args.id}")
        return 0

    issue.status = "open"
    issue.updated = now_utc()
    issue.closed_reason = ""
    spec.save(config_path)

    output.success(f"Reopened: {args.id}")
    output.json_output({"id": args.id, "status": "open"})

    return 0


def _print_issue_summary(issue: Issue, output: Output) -> None:
    """Print a one-line issue summary."""
    if output.quiet:
        return
    status_icon = "○" if issue.status == "open" else "✓"
    print(f"{status_icon} [{issue.id}] {issue.text}")


def _print_issue_detail(issue: Issue, output: Output) -> None:
    """Print detailed issue info."""
    if output.quiet:
        return
    print(f"ID:      {issue.id}")
    print(f"Text:    {issue.text}")
    print(f"Status:  {issue.status}")
    if issue.tags:
        print(f"Tags:    {', '.join(issue.tags)}")
    if issue.closed_reason:
        print(f"Reason:  {issue.closed_reason}")
    print(f"Created: {issue.created}")
    if issue.updated:
        print(f"Updated: {issue.updated}")


def _parse_list(value: str | None) -> list[str]:
    """Parse comma-separated values."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]
