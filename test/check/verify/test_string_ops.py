"""Tests for string/list operators: in, match, empty, exists."""

from __future__ import annotations

from datetime import datetime, timezone

from certo.check.core import Evidence
from certo.check.fact import FactEvidence
from certo.check.verify import Verify, verify_claim


def test_in_string_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test in operator with string passes."""
    verify = Verify.parse({"k-pytest.stdout": {"in": "passed"}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_in_string_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test in operator with string fails."""
    verify = Verify.parse({"k-pytest.stdout": {"in": "failed"}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_in_list_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test in operator with list passes."""
    evidence_map["k-facts"] = FactEvidence(
        check_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"versions": ["3.11", "3.12", "3.13"]},
    )
    verify = Verify.parse({"k-facts.facts.versions": {"in": "3.12"}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_in_list_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test in operator with list fails."""
    evidence_map["k-facts"] = FactEvidence(
        check_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"versions": ["3.11", "3.12"]},
    )
    verify = Verify.parse({"k-facts.facts.versions": {"in": "3.10"}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_value_in_expected_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test checking if a scalar is in an expected list."""
    verify = Verify.parse({"k-pytest.exit_code": {"in": [0, 1, 2]}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_value_in_expected_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test checking if a scalar is not in expected list."""
    verify = Verify.parse({"k-pytest.exit_code": {"in": [1, 2, 3]}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_match_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test match operator passes."""
    verify = Verify.parse({"k-pytest.stdout": {"match": r"\d+ passed"}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_match_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test match operator fails."""
    verify = Verify.parse({"k-pytest.stdout": {"match": r"\d+ failed"}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_match_non_string(evidence_map: dict[str, Evidence]) -> None:
    """Test match operator on non-string fails."""
    verify = Verify.parse({"k-pytest.exit_code": {"match": r"\d+"}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed
    assert any("expected string" in d for d in result.details)


def test_empty_true_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=true on empty string passes."""
    verify = Verify.parse({"k-pytest.stderr": {"empty": True}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_empty_true_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=true on non-empty string fails."""
    verify = Verify.parse({"k-pytest.stdout": {"empty": True}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_empty_false_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=false on non-empty string passes."""
    verify = Verify.parse({"k-pytest.stdout": {"empty": False}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_empty_false_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=false on empty string fails."""
    verify = Verify.parse({"k-pytest.stderr": {"empty": False}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_empty_list_true(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=true on empty list passes."""
    evidence_map["k-facts"] = FactEvidence(
        check_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"items": []},
    )
    verify = Verify.parse({"k-facts.facts.items": {"empty": True}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_empty_list_false(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=false on non-empty list passes."""
    evidence_map["k-facts"] = FactEvidence(
        check_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"items": ["a", "b"]},
    )
    verify = Verify.parse({"k-facts.facts.items": {"empty": False}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_empty_dict_true(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=true on empty dict passes."""
    evidence_map["k-facts"] = FactEvidence(
        check_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"items": {}},
    )
    verify = Verify.parse({"k-facts.facts.items": {"empty": True}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_empty_true_on_falsy_value(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=true on falsy non-string/list/dict value."""
    verify = Verify.parse({"k-pytest.exit_code": {"empty": True}})
    result = verify_claim(verify, evidence_map)
    assert result.passed  # 0 is falsy


def test_empty_false_on_truthy_value(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=false on truthy non-string/list/dict value."""
    verify = Verify.parse({"k-failing.exit_code": {"empty": False}})
    result = verify_claim(verify, evidence_map)
    assert result.passed  # 1 is truthy


def test_empty_false_on_falsy_value(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=false fails on falsy value."""
    verify = Verify.parse({"k-pytest.exit_code": {"empty": False}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed  # 0 is falsy


def test_empty_list_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=false on empty list fails."""
    evidence_map["k-facts"] = FactEvidence(
        check_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"items": []},
    )
    verify = Verify.parse({"k-facts.facts.items": {"empty": False}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_empty_dict_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test empty=false on empty dict fails."""
    evidence_map["k-facts"] = FactEvidence(
        check_id="k-facts",
        kind="fact",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        facts={"items": {}},
    )
    verify = Verify.parse({"k-facts.facts.items": {"empty": False}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed


def test_exists_true_pass(evidence_map: dict[str, Evidence]) -> None:
    """Test exists=true passes when value exists."""
    verify = Verify.parse({"k-pytest.exit_code": {"exists": True}})
    result = verify_claim(verify, evidence_map)
    assert result.passed


def test_exists_false_fail(evidence_map: dict[str, Evidence]) -> None:
    """Test exists=false fails when value exists."""
    verify = Verify.parse({"k-pytest.exit_code": {"exists": False}})
    result = verify_claim(verify, evidence_map)
    assert not result.passed
