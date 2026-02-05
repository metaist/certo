"""Static verification checks."""

from __future__ import annotations

import tomllib

from certo.spec import Spec
from certo.check.core import CheckContext, CheckResult


def check_blueprint_exists(ctx: CheckContext) -> CheckResult:
    """Check that a blueprint file exists."""
    if ctx.blueprint_path.exists():
        return CheckResult(
            concern_id="c1",
            claim="A spec.toml file can be parsed",
            passed=True,
            message="File exists",
            strategy="static",
        )
    return CheckResult(
        concern_id="c1",
        claim="A spec.toml file can be parsed",
        passed=False,
        message=f"File not found: {ctx.blueprint_path}",
        strategy="static",
    )


def check_blueprint_valid_toml(ctx: CheckContext) -> CheckResult:
    """Check that the blueprint is valid TOML."""
    if not ctx.blueprint_path.exists():
        return CheckResult(
            concern_id="c1",
            claim="A spec.toml file can be parsed",
            passed=False,
            message="Cannot check TOML validity: file does not exist",
            strategy="static",
        )

    try:
        with ctx.blueprint_path.open("rb") as f:
            data = tomllib.load(f)
        ctx.blueprint = Spec.parse(data)
        return CheckResult(
            concern_id="c1",
            claim="A spec.toml file can be parsed",
            passed=True,
            message="Valid TOML",
            strategy="static",
        )
    except tomllib.TOMLDecodeError as e:
        return CheckResult(
            concern_id="c1",
            claim="A spec.toml file can be parsed",
            passed=False,
            message=f"Invalid TOML: {e}",
            strategy="static",
        )
