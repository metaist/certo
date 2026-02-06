"""Tests for boolean operators: and, or, not."""

from __future__ import annotations

from certo.check.core import Evidence
from certo.check.verify import Verify, verify_claim


def test_and_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test explicit AND passes when all pass."""
    verify = Verify.parse(
        {
            "and": [
                {"k-pytest.exit_code": {"eq": 0}},
                {"k-ruff.exit_code": {"eq": 0}},
            ]
        }
    )
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_and_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test explicit AND fails when one fails."""
    verify = Verify.parse(
        {
            "and": [
                {"k-pytest.exit_code": {"eq": 0}},
                {"k-failing.exit_code": {"eq": 0}},
            ]
        }
    )
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_or_first_passes(evidence_map: dict[str, Evidence]) -> None:
    """Test OR passes when first clause passes."""
    verify = Verify.parse(
        {
            "or": [
                {"k-pytest.exit_code": {"eq": 0}},
                {"k-failing.exit_code": {"eq": 0}},
            ]
        }
    )
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_or_second_passes(evidence_map: dict[str, Evidence]) -> None:
    """Test OR passes when second clause passes."""
    verify = Verify.parse(
        {
            "or": [
                {"k-failing.exit_code": {"eq": 0}},
                {"k-pytest.exit_code": {"eq": 0}},
            ]
        }
    )
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_or_none_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test OR fails when no clause passes."""
    verify = Verify.parse(
        {
            "or": [
                {"k-failing.exit_code": {"eq": 0}},
                {"k-pytest.exit_code": {"eq": 1}},
            ]
        }
    )
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_not_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test NOT passes when inner fails."""
    verify = Verify.parse({"not": {"k-failing.stderr": {"empty": True}}})
    result = verify_claim(verify, evidence_map)
    assert result.passed  # stderr is NOT empty


def test_not_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test NOT fails when inner passes."""
    verify = Verify.parse({"not": {"k-pytest.exit_code": {"eq": 0}}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed  # exit_code IS 0


def test_implicit_and_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test multiple properties (implicit AND) pass."""
    verify = Verify.parse(
        {
            "k-pytest.exit_code": {"eq": 0},
            "k-pytest.duration": {"lt": 10},
        }
    )
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_implicit_and_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test multiple properties (implicit AND) fail when one fails."""
    verify = Verify.parse(
        {
            "k-pytest.exit_code": {"eq": 0},
            "k-pytest.duration": {"lt": 1},
        }
    )
    result = verify_claim(verify, evidence_map)
    assert not result.passed
