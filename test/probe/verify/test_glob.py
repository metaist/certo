"""Tests for glob patterns and collection operators: all, any."""

from __future__ import annotations

from certo.probe.core import Fact
from certo.probe.verify import Verify, verify_rule


def test_glob_all_pass(fact_map: dict[str, Fact]) -> None:
    """Test glob with implicit all passes."""
    # k-py* only matches k-pytest
    verify = Verify.parse({"k-py*.exit_code": {"eq": 0}})
    result = verify_rule(verify, fact_map)
    assert result.passed


def test_glob_all_fail(fact_map: dict[str, Fact]) -> None:
    """Test glob with implicit all fails when one fails."""
    # k-* matches all, including k-failing
    verify = Verify.parse({"k-*.exit_code": {"eq": 0}})
    result = verify_rule(verify, fact_map)
    assert not result.passed


def test_glob_any_pass(fact_map: dict[str, Fact]) -> None:
    """Test glob with explicit any passes."""
    verify = Verify.parse({"k-*.exit_code": {"any": {"eq": 0}}})
    result = verify_rule(verify, fact_map)
    assert result.passed  # At least one has exit_code=0


def test_glob_any_fail(fact_map: dict[str, Fact]) -> None:
    """Test glob with explicit any fails."""
    verify = Verify.parse({"k-*.exit_code": {"any": {"eq": 99}}})
    result = verify_rule(verify, fact_map)
    assert not result.passed  # None have exit_code=99


def test_glob_explicit_all_pass(fact_map: dict[str, Fact]) -> None:
    """Test glob with explicit all passes."""
    verify = Verify.parse({"k-py*.exit_code": {"all": {"eq": 0}}})
    result = verify_rule(verify, fact_map)
    assert result.passed


def test_status_code_glob(fact_map: dict[str, Fact]) -> None:
    """Test glob on status_code (only URL evidence has it)."""
    verify = Verify.parse({"*.status_code": {"lt": 400}})
    result = verify_rule(verify, fact_map)
    assert result.passed  # Only k-python-eol has status_code=200
