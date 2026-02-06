"""Tests for comparison operators: eq, ne, lt, lte, gt, gte."""

from __future__ import annotations

from certo.check.core import Evidence
from certo.check.verify import Verify, verify_claim


def test_eq_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test eq operator passes."""
    verify = Verify.parse({"k-pytest.exit_code": {"eq": 0}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_eq_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test eq operator fails."""
    verify = Verify.parse({"k-pytest.exit_code": {"eq": 1}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed
    assert any("expected = 1" in d for d in result.details)


def test_ne_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test ne operator passes."""
    verify = Verify.parse({"k-pytest.exit_code": {"ne": 1}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_ne_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test ne operator fails."""
    verify = Verify.parse({"k-pytest.exit_code": {"ne": 0}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_lt_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test lt operator passes."""
    verify = Verify.parse({"k-pytest.duration": {"lt": 10}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_lt_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test lt operator fails."""
    verify = Verify.parse({"k-pytest.duration": {"lt": 5}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed
    assert any("expected < 5" in d for d in result.details)


def test_lte_pass_equal(evidence_map: dict[str, Evidence]) -> None:
    """Test lte operator passes on equal value."""
    verify = Verify.parse({"k-pytest.duration": {"lte": 7.2}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_lte_pass_less(evidence_map: dict[str, Evidence]) -> None:
    """Test lte operator passes on less value."""
    verify = Verify.parse({"k-pytest.duration": {"lte": 10}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_gt_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test gt operator passes."""
    verify = Verify.parse({"k-pytest.duration": {"gt": 5}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_gt_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test gt operator fails."""
    verify = Verify.parse({"k-pytest.duration": {"gt": 10}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_gte_pass_equal(evidence_map: dict[str, Evidence]) -> None:
    """Test gte operator passes on equal value."""
    verify = Verify.parse({"k-pytest.json.totals.percent_covered": {"gte": 100}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_gte_pass_greater(evidence_map: dict[str, Evidence]) -> None:
    """Test gte operator passes on greater value."""
    verify = Verify.parse({"k-pytest.json.totals.percent_covered": {"gte": 98}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_gte_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test gte operator fails."""
    verify = Verify.parse({"k-pytest.json.totals.percent_covered": {"gte": 101}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_multiple_ops_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test multiple operators on same selector pass."""
    verify = Verify.parse(
        {"k-pytest.json.totals.percent_covered": {"gte": 98, "lte": 100}}
    )
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_multiple_ops_one_fails(evidence_map: dict[str, Evidence]) -> None:
    """Test multiple operators fail when one fails."""
    verify = Verify.parse(
        {"k-pytest.json.totals.percent_covered": {"gte": 98, "lte": 99}}
    )
    result = verify_claim(verify, evidence_map)
    assert not result.passed
