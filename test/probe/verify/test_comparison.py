"""Tests for comparison operators: eq, ne, lt, lte, gt, gte."""

from __future__ import annotations

from certo.probe.core import Fact
from certo.probe.verify import Verify, verify_claim


def test_eq_pass(fact_map: dict[str, Fact]) -> None:
    """Test eq operator passes."""
    verify = Verify.parse({"k-pytest.exit_code": {"eq": 0}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_eq_fail(fact_map: dict[str, Fact]) -> None:
    """Test eq operator fails."""
    verify = Verify.parse({"k-pytest.exit_code": {"eq": 1}})
    result = verify_claim(verify, fact_map)
    assert not result.passed
    assert any("expected = 1" in d for d in result.details)


def test_ne_pass(fact_map: dict[str, Fact]) -> None:
    """Test ne operator passes."""
    verify = Verify.parse({"k-pytest.exit_code": {"ne": 1}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_ne_fail(fact_map: dict[str, Fact]) -> None:
    """Test ne operator fails."""
    verify = Verify.parse({"k-pytest.exit_code": {"ne": 0}})
    result = verify_claim(verify, fact_map)
    assert not result.passed


def test_lt_pass(fact_map: dict[str, Fact]) -> None:
    """Test lt operator passes."""
    verify = Verify.parse({"k-pytest.duration": {"lt": 10}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_lt_fail(fact_map: dict[str, Fact]) -> None:
    """Test lt operator fails."""
    verify = Verify.parse({"k-pytest.duration": {"lt": 5}})
    result = verify_claim(verify, fact_map)
    assert not result.passed
    assert any("expected < 5" in d for d in result.details)


def test_lte_pass_equal(fact_map: dict[str, Fact]) -> None:
    """Test lte operator passes on equal value."""
    verify = Verify.parse({"k-pytest.duration": {"lte": 7.2}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_lte_pass_less(fact_map: dict[str, Fact]) -> None:
    """Test lte operator passes on less value."""
    verify = Verify.parse({"k-pytest.duration": {"lte": 10}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_gt_pass(fact_map: dict[str, Fact]) -> None:
    """Test gt operator passes."""
    verify = Verify.parse({"k-pytest.duration": {"gt": 5}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_gt_fail(fact_map: dict[str, Fact]) -> None:
    """Test gt operator fails."""
    verify = Verify.parse({"k-pytest.duration": {"gt": 10}})
    result = verify_claim(verify, fact_map)
    assert not result.passed


def test_gte_pass_equal(fact_map: dict[str, Fact]) -> None:
    """Test gte operator passes on equal value."""
    verify = Verify.parse({"k-pytest.json.totals.percent_covered": {"gte": 100}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_gte_pass_greater(fact_map: dict[str, Fact]) -> None:
    """Test gte operator passes on greater value."""
    verify = Verify.parse({"k-pytest.json.totals.percent_covered": {"gte": 98}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_gte_fail(fact_map: dict[str, Fact]) -> None:
    """Test gte operator fails."""
    verify = Verify.parse({"k-pytest.json.totals.percent_covered": {"gte": 101}})
    result = verify_claim(verify, fact_map)
    assert not result.passed


def test_multiple_ops_pass(fact_map: dict[str, Fact]) -> None:
    """Test multiple operators on same selector pass."""
    verify = Verify.parse(
        {"k-pytest.json.totals.percent_covered": {"gte": 98, "lte": 100}}
    )
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_multiple_ops_one_fails(fact_map: dict[str, Fact]) -> None:
    """Test multiple operators fail when one fails."""
    verify = Verify.parse(
        {"k-pytest.json.totals.percent_covered": {"gte": 98, "lte": 99}}
    )
    result = verify_claim(verify, fact_map)
    assert not result.passed
