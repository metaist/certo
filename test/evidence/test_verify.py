"""Tests for verification logic."""

from datetime import datetime, timezone

import pytest

from certo.evidence.types import Evidence, ShellEvidence, UrlEvidence
from certo.evidence.verify import Verify, verify_claim


@pytest.fixture
def evidence_map() -> dict[str, Evidence]:
    """Create a sample evidence map for testing."""
    now = datetime.now(timezone.utc)
    return {
        "k-pytest": ShellEvidence(
            check_id="k-pytest",
            kind="shell",
            timestamp=now,
            duration=7.2,
            exit_code=0,
            stdout="411 passed in 7.2s",
            stderr="",
            json={
                "totals": {"percent_covered": 100.0},
            },
        ),
        "k-ruff": ShellEvidence(
            check_id="k-ruff",
            kind="shell",
            timestamp=now,
            duration=0.3,
            exit_code=0,
            stdout="All checks passed!",
            stderr="",
        ),
        "k-failing": ShellEvidence(
            check_id="k-failing",
            kind="shell",
            timestamp=now,
            duration=1.0,
            exit_code=1,
            stdout="",
            stderr="Error: something went wrong",
        ),
        "k-python-eol": UrlEvidence(
            check_id="k-python-eol",
            kind="url",
            timestamp=now,
            duration=0.5,
            status_code=200,
            body="[]",
        ),
    }


class TestOperatorEq:
    """Tests for eq operator."""

    def test_eq_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.exit_code": {"eq": 0}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_eq_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.exit_code": {"eq": 1}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed
        assert any("expected = 1" in d for d in result.details)


class TestOperatorNe:
    """Tests for ne operator."""

    def test_ne_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.exit_code": {"ne": 1}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_ne_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.exit_code": {"ne": 0}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestOperatorLt:
    """Tests for lt operator."""

    def test_lt_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.duration": {"lt": 10}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_lt_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.duration": {"lt": 5}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed
        assert any("expected < 5" in d for d in result.details)


class TestOperatorLte:
    """Tests for lte operator."""

    def test_lte_pass_equal(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.duration": {"lte": 7.2}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_lte_pass_less(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.duration": {"lte": 10}})
        result = verify_claim(verify, evidence_map)
        assert result.passed


class TestOperatorGt:
    """Tests for gt operator."""

    def test_gt_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.duration": {"gt": 5}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_gt_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.duration": {"gt": 10}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestOperatorGte:
    """Tests for gte operator."""

    def test_gte_pass_equal(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.json.totals.percent_covered": {"gte": 100}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_gte_pass_greater(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.json.totals.percent_covered": {"gte": 98}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_gte_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.json.totals.percent_covered": {"gte": 101}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestOperatorIn:
    """Tests for in operator."""

    def test_in_string_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.stdout": {"in": "passed"}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_in_string_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.stdout": {"in": "failed"}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestOperatorMatch:
    """Tests for match operator."""

    def test_match_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.stdout": {"match": r"\d+ passed"}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_match_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.stdout": {"match": r"\d+ failed"}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed

    def test_match_non_string(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.exit_code": {"match": r"\d+"}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed
        assert any("expected string" in d for d in result.details)


class TestOperatorEmpty:
    """Tests for empty operator."""

    def test_empty_true_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.stderr": {"empty": True}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_empty_true_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.stdout": {"empty": True}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed

    def test_empty_false_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.stdout": {"empty": False}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_empty_false_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.stderr": {"empty": False}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestOperatorExists:
    """Tests for exists operator."""

    def test_exists_true_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.exit_code": {"exists": True}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_exists_false_pass(self, evidence_map: dict[str, Evidence]) -> None:
        # exists=false on existing value should fail
        verify = Verify.parse({"k-pytest.exit_code": {"exists": False}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestMissingEvidence:
    """Tests for missing evidence handling."""

    def test_missing_check(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-nonexistent.exit_code": {"eq": 0}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed
        assert any("missing evidence" in d for d in result.details)

    def test_missing_path(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.nonexistent": {"eq": 0}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestMultipleProperties:
    """Tests for multiple properties (implicit AND)."""

    def test_multiple_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse(
            {
                "k-pytest.exit_code": {"eq": 0},
                "k-pytest.duration": {"lt": 10},
            }
        )
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_multiple_one_fails(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse(
            {
                "k-pytest.exit_code": {"eq": 0},
                "k-pytest.duration": {"lt": 1},  # Will fail
            }
        )
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestBooleanAnd:
    """Tests for explicit AND."""

    def test_and_pass(self, evidence_map: dict[str, Evidence]) -> None:
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

    def test_and_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse(
            {
                "and": [
                    {"k-pytest.exit_code": {"eq": 0}},
                    {"k-failing.exit_code": {"eq": 0}},  # Will fail
                ]
            }
        )
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestBooleanOr:
    """Tests for OR."""

    def test_or_first_passes(self, evidence_map: dict[str, Evidence]) -> None:
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

    def test_or_second_passes(self, evidence_map: dict[str, Evidence]) -> None:
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

    def test_or_none_pass(self, evidence_map: dict[str, Evidence]) -> None:
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


class TestBooleanNot:
    """Tests for NOT."""

    def test_not_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"not": {"k-failing.stderr": {"empty": True}}})
        result = verify_claim(verify, evidence_map)
        assert result.passed  # stderr is NOT empty, so NOT(empty=true) passes

    def test_not_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"not": {"k-pytest.exit_code": {"eq": 0}}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed  # exit_code IS 0, so NOT(eq=0) fails


class TestGlobAll:
    """Tests for glob with implicit all."""

    def test_all_pass(self, evidence_map: dict[str, Evidence]) -> None:
        # All shell checks have exit_code (pytest=0, ruff=0, failing=1)
        # But we only check pytest and ruff here
        verify = Verify.parse({"k-py*.exit_code": {"eq": 0}})
        result = verify_claim(verify, evidence_map)
        assert result.passed  # Only matches k-pytest

    def test_all_fail(self, evidence_map: dict[str, Evidence]) -> None:
        # k-* matches all, including k-failing which has exit_code=1
        verify = Verify.parse({"k-*.exit_code": {"eq": 0}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestGlobAny:
    """Tests for glob with explicit any."""

    def test_any_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-*.exit_code": {"any": {"eq": 0}}})
        result = verify_claim(verify, evidence_map)
        assert result.passed  # At least one has exit_code=0

    def test_any_fail(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-*.exit_code": {"any": {"eq": 99}}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed  # None have exit_code=99


class TestGlobExplicitAll:
    """Tests for glob with explicit all."""

    def test_explicit_all_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-py*.exit_code": {"all": {"eq": 0}}})
        result = verify_claim(verify, evidence_map)
        assert result.passed


class TestUnknownOperator:
    """Tests for unknown operator handling."""

    def test_unknown_operator(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"k-pytest.exit_code": {"foo": 0}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed
        assert any("unknown operator" in d for d in result.details)


class TestMultipleOperators:
    """Tests for multiple operators on same selector."""

    def test_multiple_ops_pass(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse(
            {"k-pytest.json.totals.percent_covered": {"gte": 98, "lte": 100}}
        )
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_multiple_ops_one_fails(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse(
            {
                "k-pytest.json.totals.percent_covered": {
                    "gte": 98,
                    "lte": 99,
                }  # 100 > 99
            }
        )
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestStatusCodeGlob:
    """Tests for status_code glob (URL evidence)."""

    def test_status_code_glob(self, evidence_map: dict[str, Evidence]) -> None:
        verify = Verify.parse({"*.status_code": {"lt": 400}})
        result = verify_claim(verify, evidence_map)
        assert result.passed  # Only k-python-eol has status_code, and it's 200


class TestOperatorInList:
    """Tests for in operator with lists."""

    def test_in_list_pass(self, evidence_map: dict[str, Evidence]) -> None:
        """Test value in list."""
        # Add evidence with a list
        from datetime import datetime, timezone
        from certo.evidence.types import FactEvidence

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

    def test_in_list_fail(self, evidence_map: dict[str, Evidence]) -> None:
        """Test value not in list."""
        from datetime import datetime, timezone
        from certo.evidence.types import FactEvidence

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


class TestOperatorInValue:
    """Tests for in operator checking if value is in expected list."""

    def test_value_in_expected_pass(self, evidence_map: dict[str, Evidence]) -> None:
        """Test checking if a scalar is in an expected list."""
        verify = Verify.parse({"k-pytest.exit_code": {"in": [0, 1, 2]}})
        result = verify_claim(verify, evidence_map)
        assert result.passed

    def test_value_in_expected_fail(self, evidence_map: dict[str, Evidence]) -> None:
        """Test checking if a scalar is not in expected list."""
        verify = Verify.parse({"k-pytest.exit_code": {"in": [1, 2, 3]}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed


class TestEmptyListDict:
    """Tests for empty operator on lists and dicts."""

    def test_empty_list_true(self, evidence_map: dict[str, Evidence]) -> None:
        """Test empty=true on empty list."""
        from datetime import datetime, timezone
        from certo.evidence.types import FactEvidence

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

    def test_empty_list_false(self, evidence_map: dict[str, Evidence]) -> None:
        """Test empty=false on non-empty list."""
        from datetime import datetime, timezone
        from certo.evidence.types import FactEvidence

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

    def test_empty_dict_true(self, evidence_map: dict[str, Evidence]) -> None:
        """Test empty=true on empty dict."""
        from datetime import datetime, timezone
        from certo.evidence.types import FactEvidence

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


class TestVerifyToDict:
    """Tests for Verify serialization."""

    def test_to_dict(self) -> None:
        """Test Verify.to_dict()."""
        verify = Verify.parse({"k-pytest.exit_code": {"eq": 0}})
        d = verify.to_dict()
        assert d == {"k-pytest.exit_code": {"eq": 0}}


class TestEmptyNonStringListDict:
    """Tests for empty operator on non-string/list/dict values."""

    def test_empty_true_on_falsy_value(self, evidence_map: dict[str, Evidence]) -> None:
        """Test empty=true on falsy non-string/list/dict value (e.g., 0)."""
        # exit_code=0 is falsy
        verify = Verify.parse({"k-pytest.exit_code": {"empty": True}})
        result = verify_claim(verify, evidence_map)
        assert result.passed  # 0 is falsy, so "empty"

    def test_empty_false_on_truthy_value(
        self, evidence_map: dict[str, Evidence]
    ) -> None:
        """Test empty=false on truthy non-string/list/dict value."""
        verify = Verify.parse({"k-failing.exit_code": {"empty": False}})
        result = verify_claim(verify, evidence_map)
        assert result.passed  # exit_code=1 is truthy

    def test_empty_false_on_falsy_value(
        self, evidence_map: dict[str, Evidence]
    ) -> None:
        """Test empty=false fails on falsy value."""
        verify = Verify.parse({"k-pytest.exit_code": {"empty": False}})
        result = verify_claim(verify, evidence_map)
        assert not result.passed  # 0 is falsy

    def test_empty_list_fail(self, evidence_map: dict[str, Evidence]) -> None:
        """Test empty=false on empty list fails."""
        from datetime import datetime, timezone
        from certo.evidence.types import FactEvidence

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

    def test_empty_dict_fail(self, evidence_map: dict[str, Evidence]) -> None:
        """Test empty=false on empty dict fails."""
        from datetime import datetime, timezone
        from certo.evidence.types import FactEvidence

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
