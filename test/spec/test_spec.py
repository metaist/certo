"""Tests for Spec parsing, serialization, and operations."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.probe.shell import ShellConfig
from certo.spec import Claim, Spec


def test_spec_parse_minimal() -> None:
    """Test parsing a spec with minimal fields."""
    data = {"version": 1}
    spec = Spec.parse(data)
    assert spec.version == 1
    assert spec.checks == []
    assert spec.claims == []


def test_spec_parse_full() -> None:
    """Test parsing a spec with all fields."""
    data = {
        "version": 2,
        "probes": [{"kind": "shell", "id": "k-test", "cmd": "echo test"}],
        "claims": [{"id": "c-abc1234", "text": "Claim 1"}],
    }
    spec = Spec.parse(data)
    assert spec.version == 2
    assert len(spec.checks) == 1
    assert spec.checks[0].id == "k-test"
    assert len(spec.claims) == 1
    assert spec.claims[0].id == "c-abc1234"


def test_spec_load() -> None:
    """Test loading a spec from a file."""
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "certo.toml"
        path.write_text("""
version = 1

[[probes]]
kind = "shell"
id = "k-test"
cmd = "echo test"

[[claims]]
id = "c-abc1234"
text = "Test claim"
""")
        spec = Spec.load(path)
        assert spec.version == 1
        assert len(spec.checks) == 1
        assert len(spec.claims) == 1


def test_spec_get_claim() -> None:
    """Test getting a claim by ID."""
    data = {
        "version": 1,
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


def test_spec_get_check() -> None:
    """Test getting a check by ID."""
    spec = Spec(
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
        version=1,
        checks=[
            ShellConfig(id="k-test", cmd="echo hello"),
        ],
    )
    result = spec.to_toml()
    assert "# PROBES" in result
    assert "[[probes]]" in result
    assert 'id = "k-test"' in result
    assert 'cmd = "echo hello"' in result


def test_spec_to_toml() -> None:
    """Test spec TOML serialization."""
    spec = Spec(
        version=1,
        claims=[Claim(id="c-abc", text="Test")],
    )
    result = spec.to_toml()
    assert "# Certo Spec" in result
    assert "version = 1" in result
    assert "# CLAIMS" in result


def test_spec_save_and_load() -> None:
    """Test spec roundtrip save and load."""
    spec = Spec(
        version=1,
        checks=[ShellConfig(id="k-test", cmd="echo test")],
        claims=[Claim(id="c-abc", text="Test claim", status="confirmed")],
    )

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "certo.toml"
        spec.save(path)

        # Load it back
        loaded = Spec.load(path)
        assert loaded.version == 1
        assert len(loaded.checks) == 1
        assert loaded.checks[0].id == "k-test"
        assert len(loaded.claims) == 1
        assert loaded.claims[0].id == "c-abc"
        assert loaded.claims[0].text == "Test claim"
