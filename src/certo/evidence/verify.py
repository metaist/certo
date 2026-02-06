"""Verification logic for claims against evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from certo.evidence.selector import parse_selector, resolve_selector
from certo.evidence.types import Evidence


@dataclass
class VerifyResult:
    """Result of verifying a claim."""

    passed: bool
    message: str = ""
    details: list[str] = field(default_factory=list)


@dataclass
class Verify:
    """A verification rule for a claim.

    Supports:
    - Single property: {"k-pytest.exit_code": {"eq": 0}}
    - Multiple properties (implicit AND): {"k-pytest.exit_code": {"eq": 0}, "k-pytest.stderr": {"empty": true}}
    - Boolean: {"and": [...], "or": [...], "not": {...}}
    - Collection: {"all": {...}, "any": {...}} for glob results
    """

    rules: dict[str, Any]

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Verify:
        """Parse verification rules from TOML data."""
        return cls(rules=data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.rules


def verify_claim(
    verify: Verify,
    evidence_map: dict[str, Evidence],
) -> VerifyResult:
    """Verify a claim against evidence.

    Args:
        verify: Verification rules
        evidence_map: Dict mapping check_id to Evidence

    Returns:
        VerifyResult indicating pass/fail with details
    """
    return _evaluate_rules(verify.rules, evidence_map)


def _evaluate_rules(
    rules: dict[str, Any],
    evidence_map: dict[str, Evidence],
) -> VerifyResult:
    """Evaluate verification rules against evidence."""
    # Check for boolean operators at top level
    if "and" in rules:
        return _evaluate_and(rules["and"], evidence_map)
    if "or" in rules:
        return _evaluate_or(rules["or"], evidence_map)
    if "not" in rules:
        return _evaluate_not(rules["not"], evidence_map)

    # Otherwise, treat as selector rules (implicit AND)
    details: list[str] = []
    all_passed = True

    for selector_str, ops in rules.items():
        result = _evaluate_selector(selector_str, ops, evidence_map)
        if not result.passed:
            all_passed = False
        details.extend(result.details)

    return VerifyResult(
        passed=all_passed,
        message="" if all_passed else "Verification failed",
        details=details,
    )


def _evaluate_and(
    clauses: list[dict[str, Any]],
    evidence_map: dict[str, Evidence],
) -> VerifyResult:
    """Evaluate AND of multiple rule sets."""
    details: list[str] = []
    for clause in clauses:
        result = _evaluate_rules(clause, evidence_map)
        details.extend(result.details)
        if not result.passed:
            return VerifyResult(passed=False, message="AND failed", details=details)
    return VerifyResult(passed=True, details=details)


def _evaluate_or(
    clauses: list[dict[str, Any]],
    evidence_map: dict[str, Evidence],
) -> VerifyResult:
    """Evaluate OR of multiple rule sets."""
    details: list[str] = []
    for clause in clauses:
        result = _evaluate_rules(clause, evidence_map)
        details.extend(result.details)
        if result.passed:
            return VerifyResult(passed=True, details=details)
    return VerifyResult(
        passed=False, message="OR failed: no clause passed", details=details
    )


def _evaluate_not(
    clause: dict[str, Any],
    evidence_map: dict[str, Evidence],
) -> VerifyResult:
    """Evaluate NOT of a rule set."""
    result = _evaluate_rules(clause, evidence_map)
    if result.passed:
        return VerifyResult(
            passed=False,
            message="NOT failed: inner clause passed",
            details=result.details,
        )
    return VerifyResult(passed=True, details=result.details)


def _evaluate_selector(
    selector_str: str,
    ops: dict[str, Any],
    evidence_map: dict[str, Evidence],
) -> VerifyResult:
    """Evaluate a selector with its operators against evidence."""
    selector = parse_selector(selector_str)
    matches = resolve_selector(selector, evidence_map)

    if not matches:
        return VerifyResult(
            passed=False,
            message=f"missing evidence: {selector_str}",
            details=[f"{selector_str}: missing evidence"],
        )

    # Check for collection operators
    if "any" in ops:
        return _evaluate_any(matches, ops["any"])
    if "all" in ops:
        return _evaluate_all(matches, ops["all"])

    # Default: implicit ALL for glob results
    return _evaluate_all(matches, ops)


def _evaluate_any(
    matches: list[tuple[str, Any]],
    ops: dict[str, Any],
) -> VerifyResult:
    """At least one match must satisfy the operators."""
    details: list[str] = []
    for path, value in matches:
        result = _check_operators(path, value, ops)
        details.extend(result.details)
        if result.passed:
            return VerifyResult(passed=True, details=details)

    return VerifyResult(
        passed=False,
        message="no match satisfied conditions",
        details=details,
    )


def _evaluate_all(
    matches: list[tuple[str, Any]],
    ops: dict[str, Any],
) -> VerifyResult:
    """All matches must satisfy the operators."""
    details: list[str] = []
    all_passed = True

    for path, value in matches:
        result = _check_operators(path, value, ops)
        details.extend(result.details)
        if not result.passed:
            all_passed = False

    return VerifyResult(
        passed=all_passed,
        message="" if all_passed else "not all matches satisfied conditions",
        details=details,
    )


def _check_operators(
    path: str,
    value: Any,
    ops: dict[str, Any],
) -> VerifyResult:
    """Check all operators against a value."""
    details: list[str] = []
    all_passed = True

    for op, expected in ops.items():
        passed, msg = _apply_operator(op, value, expected)
        detail = f"{path}: {msg}"
        details.append(detail)
        if not passed:
            all_passed = False

    return VerifyResult(passed=all_passed, details=details)


def _apply_operator(op: str, value: Any, expected: Any) -> tuple[bool, str]:
    """Apply a single operator, returning (passed, message)."""
    match op:
        # Comparison operators
        case "eq":
            passed = value == expected
            return (
                passed,
                f"expected = {expected}, got {value}"
                if not passed
                else f"= {expected} ✓",
            )

        case "ne":
            passed = value != expected
            return (
                passed,
                f"expected ≠ {expected}, got {value}"
                if not passed
                else f"≠ {expected} ✓",
            )

        case "lt":
            passed = value < expected
            return (
                passed,
                f"expected < {expected}, got {value}"
                if not passed
                else f"< {expected} ✓",
            )

        case "lte":
            passed = value <= expected
            return (
                passed,
                f"expected ≤ {expected}, got {value}"
                if not passed
                else f"≤ {expected} ✓",
            )

        case "gt":
            passed = value > expected
            return (
                passed,
                f"expected > {expected}, got {value}"
                if not passed
                else f"> {expected} ✓",
            )

        case "gte":
            passed = value >= expected
            return (
                passed,
                f"expected ≥ {expected}, got {value}"
                if not passed
                else f"≥ {expected} ✓",
            )

        # String/list operators
        case "in":
            if isinstance(value, str):
                passed = expected in value
                return (
                    passed,
                    f"expected '{expected}' in string, not found"
                    if not passed
                    else f"contains '{expected}' ✓",
                )
            elif isinstance(value, list):
                passed = expected in value
                return (
                    passed,
                    f"expected {expected} in list, not found"
                    if not passed
                    else f"contains {expected} ✓",
                )
            else:
                # Check if value is in expected (for "value in [list]" pattern)
                passed = value in expected
                return (
                    passed,
                    f"expected {value} in {expected}, not found"
                    if not passed
                    else f"{value} in {expected} ✓",
                )

        case "match":
            if not isinstance(value, str):
                return (False, f"expected string for match, got {type(value).__name__}")
            passed = bool(re.search(expected, value))
            return (
                passed,
                f"expected to match /{expected}/, did not"
                if not passed
                else f"matches /{expected}/ ✓",
            )

        case "empty":
            if expected:  # empty = true
                if isinstance(value, str):
                    passed = value == ""
                elif isinstance(value, (list, dict)):
                    passed = len(value) == 0
                else:
                    passed = not value
                return (
                    passed,
                    f"expected empty, got {repr(value)[:50]}"
                    if not passed
                    else "empty ✓",
                )
            else:  # empty = false
                if isinstance(value, str):
                    passed = value != ""
                elif isinstance(value, (list, dict)):
                    passed = len(value) > 0
                else:
                    passed = bool(value)
                return (
                    passed,
                    "expected non-empty, got empty" if not passed else "non-empty ✓",
                )

        # Existence operator
        case "exists":
            # If we got here, the value exists (selector resolved)
            passed = expected  # exists = true means we want it to exist
            return (passed, "exists ✓" if passed else "expected not to exist")

        case _:
            return (False, f"unknown operator: {op}")
