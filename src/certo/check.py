"""Blueprint verification checks."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    """Result of a single verification check."""

    concern_id: str
    claim: str
    passed: bool
    message: str
    strategy: str


def check_blueprint_exists(blueprint_path: Path) -> CheckResult:
    """Check that a blueprint file exists."""
    if blueprint_path.exists():
        return CheckResult(
            concern_id="c1",
            claim="A blueprint.toml file can be parsed",
            passed=True,
            message="File exists",
            strategy="static",
        )
    return CheckResult(
        concern_id="c1",
        claim="A blueprint.toml file can be parsed",
        passed=False,
        message=f"File not found: {blueprint_path}",
        strategy="static",
    )


def check_blueprint_valid_toml(blueprint_path: Path) -> CheckResult:
    """Check that the blueprint is valid TOML."""
    if not blueprint_path.exists():
        return CheckResult(
            concern_id="c1",
            claim="A blueprint.toml file can be parsed",
            passed=False,
            message="Cannot check TOML validity: file does not exist",
            strategy="static",
        )

    try:
        with blueprint_path.open("rb") as f:
            tomllib.load(f)
        return CheckResult(
            concern_id="c1",
            claim="A blueprint.toml file can be parsed",
            passed=True,
            message="Valid TOML",
            strategy="static",
        )
    except tomllib.TOMLDecodeError as e:
        return CheckResult(
            concern_id="c1",
            claim="A blueprint.toml file can be parsed",
            passed=False,
            message=f"Invalid TOML: {e}",
            strategy="static",
        )


def check_blueprint(blueprint_path: Path) -> list[CheckResult]:
    """Run all blueprint checks and return results."""
    results: list[CheckResult] = []

    # c1: Blueprint can be parsed
    exists_result = check_blueprint_exists(blueprint_path)
    if not exists_result.passed:
        results.append(exists_result)
        return results

    toml_result = check_blueprint_valid_toml(blueprint_path)
    results.append(toml_result)

    return results
