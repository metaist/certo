"""Tests for miscellaneous verification features."""

from __future__ import annotations

from certo.check.core import Evidence
from certo.check.verify import Verify, verify_claim


def test_missing_check(evidence_map: dict[str, Evidence]) -> None:
    """Test missing check returns failure."""
    verify = Verify.parse({"k-nonexistent.exit_code": {"eq": 0}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed
    assert any("missing evidence" in d for d in result.details)


def test_missing_path(evidence_map: dict[str, Evidence]) -> None:
    """Test missing path returns failure."""
    verify = Verify.parse({"k-pytest.nonexistent": {"eq": 0}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_unknown_operator(evidence_map: dict[str, Evidence]) -> None:
    """Test unknown operator returns failure."""
    verify = Verify.parse({"k-pytest.exit_code": {"foo": 0}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed
    assert any("unknown operator" in d for d in result.details)


def test_verify_to_dict() -> None:
    """Test Verify.to_dict() serialization."""
    verify = Verify.parse({"k-pytest.exit_code": {"eq": 0}})
    d = verify.to_dict()
    assert d == {"k-pytest.exit_code": {"eq": 0}}
