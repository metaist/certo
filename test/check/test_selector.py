"""Tests for selector parsing and resolution."""

from datetime import datetime, timezone

import pytest

from certo.check.core import Evidence
from certo.check.selector import parse_selector, resolve_selector, Selector
from certo.check.shell import ShellEvidence
from certo.check.url import UrlEvidence


def test_parse_simple_selector() -> None:
    """Test parsing simple dot-separated selector."""
    sel = parse_selector("k-pytest.exit_code")
    assert sel.segments == ["k-pytest", "exit_code"]


def test_parse_deep_selector() -> None:
    """Test parsing deeply nested selector."""
    sel = parse_selector("k-pytest.json.totals.percent_covered")
    assert sel.segments == ["k-pytest", "json", "totals", "percent_covered"]


def test_parse_bracket_selector() -> None:
    """Test parsing selector with bracket notation."""
    sel = parse_selector("k-pytest.json.files[src/certo/cli.py].percent_covered")
    assert sel.segments == [
        "k-pytest",
        "json",
        "files",
        "src/certo/cli.py",
        "percent_covered",
    ]


def test_parse_all_brackets() -> None:
    """Test parsing selector with all brackets."""
    sel = parse_selector("[k-pytest][json][files]")
    assert sel.segments == ["k-pytest", "json", "files"]


def test_parse_mixed_notation() -> None:
    """Test parsing selector mixing dots and brackets."""
    sel = parse_selector("k-pytest[json].files[src/foo.py]")
    assert sel.segments == ["k-pytest", "json", "files", "src/foo.py"]


def test_parse_glob_selector() -> None:
    """Test parsing selector with glob."""
    sel = parse_selector("*.exit_code")
    assert sel.segments == ["*", "exit_code"]


def test_parse_glob_in_segment() -> None:
    """Test parsing selector with glob in middle of segment."""
    sel = parse_selector("k-py*.exit_code")
    assert sel.segments == ["k-py*", "exit_code"]


def test_parse_glob_in_brackets() -> None:
    """Test parsing selector with glob in brackets."""
    sel = parse_selector("k-pytest.json.files[*.py].percent_covered")
    assert sel.segments == ["k-pytest", "json", "files", "*.py", "percent_covered"]


def test_parse_unclosed_bracket() -> None:
    """Test error on unclosed bracket."""
    with pytest.raises(ValueError, match="Unclosed bracket"):
        parse_selector("k-pytest.files[foo")


def test_selector_str() -> None:
    """Test selector string representation."""
    sel = Selector(segments=["k-pytest", "json", "files", "src/certo/cli.py"])
    # Keys with special chars should use brackets
    assert "src/certo/cli.py" in str(sel) or "[src/certo/cli.py]" in str(sel)


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
            stdout="411 passed",
            stderr="",
            json={
                "totals": {"percent_covered": 100.0, "num_statements": 2285},
                "files": {
                    "src/certo/cli.py": {"percent_covered": 98.5},
                    "src/certo/spec.py": {"percent_covered": 100.0},
                },
            },
        ),
        "k-ruff": ShellEvidence(
            check_id="k-ruff",
            kind="shell",
            timestamp=now,
            duration=0.3,
            exit_code=0,
            stdout="",
            stderr="",
        ),
        "k-python-eol": UrlEvidence(
            check_id="k-python-eol",
            kind="url",
            timestamp=now,
            duration=0.5,
            status_code=200,
            body='[{"version": "3.11"}]',
            json=[{"version": "3.11"}],
        ),
    }


def test_resolve_simple(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving simple selector."""
    results = resolve_selector("k-pytest.exit_code", evidence_map)
    assert len(results) == 1
    assert results[0] == ("k-pytest.exit_code", 0)


def test_resolve_deep(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving deep selector."""
    results = resolve_selector("k-pytest.json.totals.percent_covered", evidence_map)
    assert len(results) == 1
    assert results[0] == ("k-pytest.json.totals.percent_covered", 100.0)


def test_resolve_glob_check_id(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving glob on check IDs."""
    results = resolve_selector("*.exit_code", evidence_map)
    # Should match k-pytest and k-ruff (both have exit_code)
    assert len(results) == 2
    paths = [r[0] for r in results]
    assert "k-pytest.exit_code" in paths
    assert "k-ruff.exit_code" in paths


def test_resolve_glob_partial(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving partial glob on check IDs."""
    results = resolve_selector("k-py*.exit_code", evidence_map)
    assert len(results) == 1
    assert results[0][0] == "k-pytest.exit_code"


def test_resolve_glob_in_keys(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving glob in nested keys."""
    results = resolve_selector("k-pytest.json.files[*].percent_covered", evidence_map)
    assert len(results) == 2
    values = [r[1] for r in results]
    assert 98.5 in values
    assert 100.0 in values


def test_resolve_glob_pattern_in_keys(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving glob pattern in nested keys."""
    results = resolve_selector(
        "k-pytest.json.files[*.py].percent_covered", evidence_map
    )
    # Both files end in .py
    assert len(results) == 2


def test_resolve_missing_check(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving non-existent check."""
    results = resolve_selector("k-nonexistent.exit_code", evidence_map)
    assert len(results) == 0


def test_resolve_missing_path(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving non-existent path."""
    results = resolve_selector("k-pytest.nonexistent.path", evidence_map)
    assert len(results) == 0


def test_resolve_url_evidence(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving URL evidence."""
    results = resolve_selector("k-python-eol.status_code", evidence_map)
    assert len(results) == 1
    assert results[0] == ("k-python-eol.status_code", 200)


def test_resolve_status_code_glob(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving status_code with glob (only URL checks)."""
    results = resolve_selector("*.status_code", evidence_map)
    # Only k-python-eol has status_code
    assert len(results) == 1
    assert results[0] == ("k-python-eol.status_code", 200)


def test_resolve_list_by_index(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving list item by index."""
    results = resolve_selector("k-python-eol.json[0].version", evidence_map)
    assert len(results) == 1
    assert results[0][1] == "3.11"


def test_resolve_list_glob(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving list items with glob."""
    results = resolve_selector("k-python-eol.json[*].version", evidence_map)
    assert len(results) == 1
    assert results[0][1] == "3.11"


def test_resolve_empty_selector() -> None:
    """Test resolving empty selector."""
    results = resolve_selector("", {})
    assert len(results) == 0


def test_resolve_no_remaining_segments(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving with no remaining segments (returns whole check)."""
    results = resolve_selector("k-pytest", evidence_map)
    assert len(results) == 1
    assert results[0][0] == "k-pytest"
    assert isinstance(results[0][1], dict)


def test_resolve_list_invalid_index(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving list with invalid index."""
    results = resolve_selector("k-python-eol.json[foo]", evidence_map)
    assert len(results) == 0


def test_resolve_list_out_of_bounds(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving list with out of bounds index."""
    results = resolve_selector("k-python-eol.json[99]", evidence_map)
    assert len(results) == 0


def test_parse_leading_dot() -> None:
    """Test parsing selector with leading dot (empty first segment)."""
    sel = parse_selector(".foo.bar")
    # Leading dot means empty first segment is skipped
    assert sel.segments == ["foo", "bar"]


def test_parse_consecutive_dots() -> None:
    """Test parsing selector with consecutive dots."""
    sel = parse_selector("foo..bar")
    # Empty segments are skipped
    assert sel.segments == ["foo", "bar"]


def test_resolve_glob_empty_dict(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving glob against empty dict."""
    # Add evidence with empty json
    from datetime import datetime, timezone

    evidence_map["k-empty"] = ShellEvidence(
        check_id="k-empty",
        kind="shell",
        timestamp=datetime.now(timezone.utc),
        duration=0.1,
        exit_code=0,
        stdout="",
        stderr="",
        json={},
    )
    results = resolve_selector("k-empty.json[*]", evidence_map)
    assert len(results) == 0


def test_resolve_glob_on_list(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving glob pattern on list indices."""
    # k-python-eol.json is a list
    results = resolve_selector("k-python-eol.json[*].version", evidence_map)
    assert len(results) == 1
    assert results[0][1] == "3.11"


def test_resolve_glob_no_match_in_list(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving glob pattern that doesn't match any list index."""
    # Pattern "a*" won't match numeric indices like "0"
    results = resolve_selector("k-python-eol.json[a*]", evidence_map)
    assert len(results) == 0


def test_resolve_glob_on_scalar(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving glob on a scalar value (not dict or list)."""
    # stdout is a string, glob should return empty
    results = resolve_selector("k-pytest.stdout[*]", evidence_map)
    assert len(results) == 0


def test_resolve_glob_no_match_in_dict(evidence_map: dict[str, Evidence]) -> None:
    """Test resolving glob pattern that doesn't match any dict keys."""
    # k-pytest.json.totals exists, but pattern "foo*" won't match "percent_covered"
    results = resolve_selector("k-pytest.json.totals[foo*]", evidence_map)
    assert len(results) == 0
