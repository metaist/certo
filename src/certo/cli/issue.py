"""Issue command implementation."""

from __future__ import annotations

from argparse import Namespace

from certo.cli.output import Output
from certo.spec import Issue, Spec, generate_id, now_utc


def cmd_issue(args: Namespace, output: Output) -> int:
    """Create, close, or reopen an issue."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)

    # Handle --close
    if getattr(args, "close", None):
        return _close_issue(spec, spec_path, args.close, args, output)

    # Handle --reopen
    if getattr(args, "reopen", None):
        return _reopen_issue(spec, spec_path, args.reopen, output)

    # Create new issue
    text = getattr(args, "text", None)
    if not text:
        output.error("Issue text is required")
        return 1

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
    spec.save(spec_path)

    output.info(f"Created issue: {issue_id}")
    output.json_output({"id": issue_id, "text": text})

    return 0


def _close_issue(
    spec: Spec, spec_path: object, issue_id: str, args: Namespace, output: Output
) -> int:
    """Close an issue."""
    issue = spec.get_issue(issue_id)

    if not issue:
        output.error(f"Issue not found: {issue_id}")
        return 1

    if issue.status == "closed":
        output.info(f"Issue already closed: {issue_id}")
        return 0

    issue.status = "closed"
    issue.updated = now_utc()
    issue.closed_reason = getattr(args, "reason", "") or ""
    spec.save(spec_path)  # type: ignore[arg-type]

    output.info(f"Closed: {issue_id}")
    output.json_output({"id": issue_id, "status": "closed"})

    return 0


def _reopen_issue(spec: Spec, spec_path: object, issue_id: str, output: Output) -> int:
    """Reopen an issue."""
    issue = spec.get_issue(issue_id)

    if not issue:
        output.error(f"Issue not found: {issue_id}")
        return 1

    if issue.status == "open":
        output.info(f"Issue already open: {issue_id}")
        return 0

    issue.status = "open"
    issue.updated = now_utc()
    issue.closed_reason = ""
    spec.save(spec_path)  # type: ignore[arg-type]

    output.info(f"Reopened: {issue_id}")
    output.json_output({"id": issue_id, "status": "open"})

    return 0


def _parse_list(value: str | None) -> list[str]:
    """Parse comma-separated values."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]
