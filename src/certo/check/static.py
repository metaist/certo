"""Static verification checks."""

from __future__ import annotations

import tomllib

from certo.check.core import CheckContext, CheckResult
from certo.spec import Spec


def check_spec_exists(ctx: CheckContext) -> CheckResult:
    """Check that a spec file exists."""
    if ctx.spec_path.exists():
        return CheckResult(
            claim_id="builtin-spec-exists",
            claim_text="A spec.toml file can be parsed",
            passed=True,
            message="File exists",
            strategy="static",
        )
    return CheckResult(
        claim_id="builtin-spec-exists",
        claim_text="A spec.toml file can be parsed",
        passed=False,
        message=f"File not found: {ctx.spec_path}",
        strategy="static",
    )


def check_spec_valid_toml(ctx: CheckContext) -> CheckResult:
    """Check that the spec is valid TOML."""
    if not ctx.spec_path.exists():
        return CheckResult(
            claim_id="builtin-spec-valid",
            claim_text="A spec.toml file can be parsed",
            passed=False,
            message="Cannot check TOML validity: file does not exist",
            strategy="static",
        )

    try:
        with ctx.spec_path.open("rb") as f:
            data = tomllib.load(f)
        ctx.spec = Spec.parse(data)
        return CheckResult(
            claim_id="builtin-spec-valid",
            claim_text="A spec.toml file can be parsed",
            passed=True,
            message="Valid TOML",
            strategy="static",
        )
    except tomllib.TOMLDecodeError as e:
        return CheckResult(
            claim_id="builtin-spec-valid",
            claim_text="A spec.toml file can be parsed",
            passed=False,
            message=f"Invalid TOML: {e}",
            strategy="static",
        )


# Backward compatibility aliases
check_blueprint_exists = check_spec_exists
check_blueprint_valid_toml = check_spec_valid_toml
