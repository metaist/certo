"""Claim command implementation."""

from __future__ import annotations

from argparse import Namespace

from certo.cli.output import Output
from certo.spec import Claim, Spec, generate_id, now_utc


def cmd_claim(args: Namespace, output: Output) -> int:
    """Create, confirm, or reject a claim."""
    spec_path = args.path / ".certo" / "spec.toml"

    if not spec_path.exists():
        output.error(f"No spec found at {spec_path}")
        return 1

    spec = Spec.load(spec_path)

    # Handle --confirm
    if getattr(args, "confirm", None):
        return _confirm_claim(spec, spec_path, args.confirm, output)

    # Handle --reject
    if getattr(args, "reject", None):
        return _reject_claim(spec, spec_path, args.reject, output)

    # Create new claim
    text = getattr(args, "text", None)
    if not text:
        output.error("Claim text is required")
        return 1

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

    output.info(f"Created claim: {claim_id}")
    output.json_output({"id": claim_id, "text": text})

    return 0


def _confirm_claim(spec: Spec, spec_path: object, claim_id: str, output: Output) -> int:
    """Confirm a pending claim."""
    claim = spec.get_claim(claim_id)

    if not claim:
        output.error(f"Claim not found: {claim_id}")
        return 1

    if claim.status == "confirmed":
        output.info(f"Claim already confirmed: {claim_id}")
        return 0

    claim.status = "confirmed"
    claim.updated = now_utc()
    spec.save(spec_path)  # type: ignore[arg-type]

    output.info(f"Confirmed: {claim_id}")
    output.json_output({"id": claim_id, "status": "confirmed"})

    return 0


def _reject_claim(spec: Spec, spec_path: object, claim_id: str, output: Output) -> int:
    """Reject a claim."""
    claim = spec.get_claim(claim_id)

    if not claim:
        output.error(f"Claim not found: {claim_id}")
        return 1

    if claim.status == "rejected":
        output.info(f"Claim already rejected: {claim_id}")
        return 0

    claim.status = "rejected"
    claim.updated = now_utc()
    spec.save(spec_path)  # type: ignore[arg-type]

    output.info(f"Rejected: {claim_id}")
    output.json_output({"id": claim_id, "status": "rejected"})

    return 0


def _parse_list(value: str | None) -> list[str]:
    """Parse comma-separated values."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]
