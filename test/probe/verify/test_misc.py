"""Tests for miscellaneous verification features."""

from __future__ import annotations

from certo.probe.core import Fact
from certo.probe.verify import Verify, verify_rule


def test_missing_check(fact_map: dict[str, Fact]) -> None:
    """Test missing check returns failure."""
    verify = Verify.parse({"k-nonexistent.exit_code": {"eq": 0}})
    result = verify_rule(verify, fact_map)
    assert not result.passed
    assert any("missing fact" in d for d in result.details)


def test_missing_path(fact_map: dict[str, Fact]) -> None:
    """Test missing path returns failure."""
    verify = Verify.parse({"k-pytest.nonexistent": {"eq": 0}})
    result = verify_rule(verify, fact_map)
    assert not result.passed


def test_unknown_operator(fact_map: dict[str, Fact]) -> None:
    """Test unknown operator returns failure."""
    verify = Verify.parse({"k-pytest.exit_code": {"foo": 0}})
    result = verify_rule(verify, fact_map)
    assert not result.passed
    assert any("unknown operator" in d for d in result.details)


def test_verify_to_dict() -> None:
    """Test Verify.to_dict() serialization."""
    verify = Verify.parse({"k-pytest.exit_code": {"eq": 0}})
    d = verify.to_dict()
    assert d == {"k-pytest.exit_code": {"eq": 0}}
