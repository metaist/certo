"""Tests for string/list operators: in, match, empty, exists."""

from __future__ import annotations

from datetime import datetime, timezone

from certo.probe.core import Fact
from certo.probe.fact import ScanFact
from certo.probe.verify import Verify, verify_claim


def test_in_string_pass(fact_map: dict[str, Fact]) -> None:
    """Test in operator with string passes."""
    verify = Verify.parse({"k-pytest.stdout": {"in": "passed"}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_in_string_fail(fact_map: dict[str, Fact]) -> None:
    """Test in operator with string fails."""
    verify = Verify.parse({"k-pytest.stdout": {"in": "failed"}})
    result = verify_claim(verify, fact_map)
    assert not result.passed


def test_in_list_pass(fact_map: dict[str, Fact]) -> None:
    """Test in operator with list passes."""
    fact_map["k-facts"] = ScanFact(
        probe_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"versions": ["3.11", "3.12", "3.13"]},
    )
    verify = Verify.parse({"k-facts.facts.versions": {"in": "3.12"}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_in_list_fail(fact_map: dict[str, Fact]) -> None:
    """Test in operator with list fails."""
    fact_map["k-facts"] = ScanFact(
        probe_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"versions": ["3.11", "3.12"]},
    )
    verify = Verify.parse({"k-facts.facts.versions": {"in": "3.10"}})
    result = verify_claim(verify, fact_map)
    assert not result.passed


def test_value_in_expected_pass(fact_map: dict[str, Fact]) -> None:
    """Test checking if a scalar is in an expected list."""
    verify = Verify.parse({"k-pytest.exit_code": {"in": [0, 1, 2]}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_value_in_expected_fail(fact_map: dict[str, Fact]) -> None:
    """Test checking if a scalar is not in expected list."""
    verify = Verify.parse({"k-pytest.exit_code": {"in": [1, 2, 3]}})
    result = verify_claim(verify, fact_map)
    assert not result.passed


def test_match_pass(fact_map: dict[str, Fact]) -> None:
    """Test match operator passes."""
    verify = Verify.parse({"k-pytest.stdout": {"match": r"\d+ passed"}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_match_fail(fact_map: dict[str, Fact]) -> None:
    """Test match operator fails."""
    verify = Verify.parse({"k-pytest.stdout": {"match": r"\d+ failed"}})
    result = verify_claim(verify, fact_map)
    assert not result.passed


def test_match_non_string(fact_map: dict[str, Fact]) -> None:
    """Test match operator on non-string fails."""
    verify = Verify.parse({"k-pytest.exit_code": {"match": r"\d+"}})
    result = verify_claim(verify, fact_map)
    assert not result.passed
    assert any("expected string" in d for d in result.details)


def test_empty_true_pass(fact_map: dict[str, Fact]) -> None:
    """Test empty=true on empty string passes."""
    verify = Verify.parse({"k-pytest.stderr": {"empty": True}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_empty_true_fail(fact_map: dict[str, Fact]) -> None:
    """Test empty=true on non-empty string fails."""
    verify = Verify.parse({"k-pytest.stdout": {"empty": True}})
    result = verify_claim(verify, fact_map)
    assert not result.passed


def test_empty_false_pass(fact_map: dict[str, Fact]) -> None:
    """Test empty=false on non-empty string passes."""
    verify = Verify.parse({"k-pytest.stdout": {"empty": False}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_empty_false_fail(fact_map: dict[str, Fact]) -> None:
    """Test empty=false on empty string fails."""
    verify = Verify.parse({"k-pytest.stderr": {"empty": False}})
    result = verify_claim(verify, fact_map)
    assert not result.passed


def test_empty_list_true(fact_map: dict[str, Fact]) -> None:
    """Test empty=true on empty list passes."""
    fact_map["k-facts"] = ScanFact(
        probe_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"items": []},
    )
    verify = Verify.parse({"k-facts.facts.items": {"empty": True}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_empty_list_false(fact_map: dict[str, Fact]) -> None:
    """Test empty=false on non-empty list passes."""
    fact_map["k-facts"] = ScanFact(
        probe_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"items": ["a", "b"]},
    )
    verify = Verify.parse({"k-facts.facts.items": {"empty": False}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_empty_dict_true(fact_map: dict[str, Fact]) -> None:
    """Test empty=true on empty dict passes."""
    fact_map["k-facts"] = ScanFact(
        probe_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"items": {}},
    )
    verify = Verify.parse({"k-facts.facts.items": {"empty": True}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_empty_true_on_falsy_value(fact_map: dict[str, Fact]) -> None:
    """Test empty=true on falsy non-string/list/dict value."""
    verify = Verify.parse({"k-pytest.exit_code": {"empty": True}})
    result = verify_claim(verify, fact_map)
    assert result.passed  # 0 is falsy


def test_empty_false_on_truthy_value(fact_map: dict[str, Fact]) -> None:
    """Test empty=false on truthy non-string/list/dict value."""
    verify = Verify.parse({"k-failing.exit_code": {"empty": False}})
    result = verify_claim(verify, fact_map)
    assert result.passed  # 1 is truthy


def test_empty_false_on_falsy_value(fact_map: dict[str, Fact]) -> None:
    """Test empty=false fails on falsy value."""
    verify = Verify.parse({"k-pytest.exit_code": {"empty": False}})
    result = verify_claim(verify, fact_map)
    assert not result.passed  # 0 is falsy


def test_empty_list_fail(fact_map: dict[str, Fact]) -> None:
    """Test empty=false on empty list fails."""
    fact_map["k-facts"] = ScanFact(
        probe_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"items": []},
    )
    verify = Verify.parse({"k-facts.facts.items": {"empty": False}})
    result = verify_claim(verify, fact_map)
    assert not result.passed


def test_empty_dict_fail(fact_map: dict[str, Fact]) -> None:
    """Test empty=false on empty dict fails."""
    fact_map["k-facts"] = ScanFact(
        probe_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"items": {}},
    )
    verify = Verify.parse({"k-facts.facts.items": {"empty": False}})
    result = verify_claim(verify, fact_map)
    assert not result.passed


def test_exists_true_pass(fact_map: dict[str, Fact]) -> None:
    """Test exists=true passes when value exists."""
    verify = Verify.parse({"k-pytest.exit_code": {"exists": True}})
    result = verify_claim(verify, fact_map)
    assert result.passed


def test_exists_false_fail(fact_map: dict[str, Fact]) -> None:
    """Test exists=false fails when value exists."""
    verify = Verify.parse({"k-pytest.exit_code": {"exists": False}})
    result = verify_claim(verify, fact_map)
    assert not result.passed
