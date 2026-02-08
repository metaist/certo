"""Tests for Spec parsing, serialization, and operations."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from certo.probe.shell import ShellConfig
from certo.spec import Claim, Issue, Spec


def test_spec_parse_minimal() -> None:
    """Test parsing a spec with minimal fields."""
    data = {"spec": {"name": "test"}}
    spec = Spec.parse(data)
    assert spec.name == "test"
    assert spec.version == 1
    assert spec.created is None
    assert spec.author == ""
    assert spec.checks == []
    assert spec.claims == []
    assert spec.issues == []


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
        "checks": [{"kind": "shell", "id": "k-test", "cmd": "echo test"}],
        "claims": [{"id": "c-abc1234", "text": "Claim 1"}],
        "issues": [{"id": "i-abc1234", "text": "Issue 1"}],
    }
    spec = Spec.parse(data)
    assert spec.name == "test"
    assert spec.version == 2
    assert spec.created == dt
    assert spec.author == "metaist"
    assert len(spec.checks) == 1
    assert spec.checks[0].id == "k-test"
    assert len(spec.claims) == 1
    assert spec.claims[0].id == "c-abc1234"
    assert len(spec.issues) == 1
    assert spec.issues[0].id == "i-abc1234"


def test_spec_load() -> None:
    """Test loading a spec from a file."""
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "spec.toml"
        path.write_text("""
[spec]
name = "test"
version = 1

[[probes]]
kind = "shell"
id = "k-test"
cmd = "echo test"

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
        assert len(spec.checks) == 1
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


def test_spec_get_check() -> None:
    """Test getting a check by ID."""
    spec = Spec(
        name="test",
        version=1,
        checks=[
            ShellConfig(id="k-first", cmd="true"),
            ShellConfig(id="k-second", cmd="true"),
        ],
    )

    check = spec.get_check("k-second")
    assert check is not None
    assert check.id == "k-second"

    assert spec.get_check("k-nonexistent") is None


def test_spec_to_toml_with_checks() -> None:
    """Test spec serialization includes checks."""
    spec = Spec(
        name="test",
        version=1,
        checks=[
            ShellConfig(id="k-test", cmd="echo hello"),
        ],
    )
    result = spec.to_toml()
    assert "# CHECKS" in result
    assert "[[probes]]" in result
    assert 'id = "k-test"' in result
    assert 'cmd = "echo hello"' in result


def test_spec_to_toml() -> None:
    """Test spec TOML serialization."""
    spec = Spec(
        name="test",
        version=1,
        author="tester",
        claims=[Claim(id="c-abc", text="Test")],
        issues=[Issue(id="i-abc", text="Question?")],
    )
    result = spec.to_toml()
    assert "# Certo Spec" in result
    assert "WARNING" in result
    assert "[spec]" in result
    assert 'name = "test"' in result
    assert "# CLAIMS" in result
    assert "# ISSUES" in result


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
        checks=[ShellConfig(id="k-test", cmd="echo test")],
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
        assert len(loaded.checks) == 1
        assert loaded.checks[0].id == "k-test"
        assert len(loaded.claims) == 1
        assert loaded.claims[0].id == "c-abc"
        assert loaded.claims[0].text == "Test claim"
        assert len(loaded.issues) == 1
