"""Tests for Spec parsing, serialization, and operations."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from certo.check.shell import ShellCheck
from certo.spec import Claim, Context, Issue, Spec


def test_spec_parse_minimal() -> None:
    """Test parsing a spec with minimal fields."""
    data = {"spec": {"name": "test"}}
    spec = Spec.parse(data)
    assert spec.name == "test"
    assert spec.version == 1
    assert spec.created is None
    assert spec.author == ""
    assert spec.claims == []
    assert spec.issues == []
    assert spec.contexts == []


def test_spec_parse_full() -> None:
    """Test parsing a spec with all fields."""
    dt = datetime(2026, 2, 5, tzinfo=timezone.utc)
    data = {
        "spec": {
            "name": "test",
            "version": 2,
            "created": dt,
            "author": "metaist",
        },
        "claims": [{"id": "c-abc1234", "text": "Claim 1"}],
        "issues": [{"id": "i-abc1234", "text": "Issue 1"}],
        "contexts": [{"id": "x-abc1234", "name": "Context 1"}],
    }
    spec = Spec.parse(data)
    assert spec.name == "test"
    assert spec.version == 2
    assert spec.created == dt
    assert spec.author == "metaist"
    assert len(spec.claims) == 1
    assert spec.claims[0].id == "c-abc1234"
    assert len(spec.issues) == 1
    assert spec.issues[0].id == "i-abc1234"
    assert len(spec.contexts) == 1
    assert spec.contexts[0].id == "x-abc1234"


def test_spec_load() -> None:
    """Test loading a spec from a file."""
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "spec.toml"
        path.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"

[[issues]]
id = "i-abc1234"
text = "Test issue"
""")
        spec = Spec.load(path)
        assert spec.name == "test"
        assert spec.version == 1
        assert len(spec.claims) == 1
        assert len(spec.issues) == 1


def test_spec_get_claim() -> None:
    """Test getting a claim by ID."""
    data = {
        "spec": {"name": "test"},
        "claims": [
            {"id": "c-abc1234", "text": "Claim 1"},
            {"id": "c-def5678", "text": "Claim 2"},
        ],
    }
    spec = Spec.parse(data)
    c1 = spec.get_claim("c-abc1234")
    assert c1 is not None
    assert c1.text == "Claim 1"
    assert spec.get_claim("c-def5678") is not None
    assert spec.get_claim("c-notfound") is None


def test_spec_get_issue() -> None:
    """Test getting an issue by ID."""
    data = {
        "spec": {"name": "test"},
        "issues": [
            {"id": "i-abc1234", "text": "Issue 1"},
            {"id": "i-def5678", "text": "Issue 2"},
        ],
    }
    spec = Spec.parse(data)
    i1 = spec.get_issue("i-abc1234")
    assert i1 is not None
    assert i1.text == "Issue 1"
    assert spec.get_issue("i-def5678") is not None
    assert spec.get_issue("i-notfound") is None


def test_spec_get_context() -> None:
    """Test getting a context by ID."""
    data = {
        "spec": {"name": "test"},
        "contexts": [
            {"id": "x-abc1234", "name": "Context 1"},
            {"id": "x-def5678", "name": "Context 2"},
        ],
    }
    spec = Spec.parse(data)
    x1 = spec.get_context("x-abc1234")
    assert x1 is not None
    assert x1.name == "Context 1"
    assert spec.get_context("x-def5678") is not None
    assert spec.get_context("x-notfound") is None


def test_spec_get_check_iterates_all() -> None:
    """Test get_check iterates through multiple checks."""
    spec = Spec(
        name="test",
        version=1,
        claims=[
            Claim(
                id="c-1",
                text="Claim 1",
                status="confirmed",
                checks=[
                    ShellCheck(id="k-first", cmd="true"),
                    ShellCheck(id="k-second", cmd="true"),
                ],
            ),
            Claim(
                id="c-2",
                text="Claim 2",
                status="confirmed",
                checks=[
                    ShellCheck(id="k-target", cmd="true"),
                ],
            ),
        ],
    )

    # Should find check in second claim after iterating first
    result = spec.get_check("k-target")
    assert result is not None
    claim, check = result
    assert claim.id == "c-2"
    assert check.id == "k-target"


def test_spec_to_toml() -> None:
    """Test spec TOML serialization."""
    spec = Spec(
        name="test",
        version=1,
        author="tester",
        claims=[Claim(id="c-abc", text="Test")],
        issues=[Issue(id="i-abc", text="Question?")],
        contexts=[Context(id="x-abc", name="dev")],
    )
    result = spec.to_toml()
    assert "# Certo Spec" in result
    assert "WARNING" in result
    assert "[spec]" in result
    assert 'name = "test"' in result
    assert "# CLAIMS" in result
    assert "# ISSUES" in result
    assert "# CONTEXTS" in result


def test_spec_to_toml_with_created() -> None:
    """Test spec TOML serialization with created timestamp."""
    dt = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)
    spec = Spec(
        name="test",
        version=1,
        created=dt,
        author="tester",
    )
    result = spec.to_toml()
    assert "created = 2026-02-05T12:00:00Z" in result
    assert 'author = "tester"' in result


def test_spec_save_and_load() -> None:
    """Test spec roundtrip save and load."""
    spec = Spec(
        name="test",
        version=1,
        claims=[Claim(id="c-abc", text="Test claim", status="confirmed")],
        issues=[Issue(id="i-abc", text="Question?")],
    )

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "spec.toml"
        spec.save(path)

        # Load it back
        loaded = Spec.load(path)
        assert loaded.name == "test"
        assert loaded.version == 1
        assert len(loaded.claims) == 1
        assert loaded.claims[0].id == "c-abc"
        assert loaded.claims[0].text == "Test claim"
        assert len(loaded.issues) == 1
