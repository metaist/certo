"""Tests for Claim parsing and serialization."""

from __future__ import annotations

from datetime import datetime, timezone

from certo.spec import Claim


def test_claim_parse_minimal() -> None:
    """Test parsing a claim with minimal fields."""
    data = {"id": "c-abc1234", "text": "Test claim"}
    claim = Claim.parse(data)
    assert claim.id == "c-abc1234"
    assert claim.text == "Test claim"
    assert claim.status == "pending"
    assert claim.source == "human"
    assert claim.author == ""
    assert claim.level == "warn"
    assert claim.tags == []
    assert claim.verify is None
    assert claim.evidence == []
    assert claim.why == ""
    assert claim.considered == []
    assert claim.traces_to == []
    assert claim.supersedes == ""
    assert claim.closes == []


def test_claim_parse_full() -> None:
    """Test parsing a claim with all fields."""
    dt = datetime(2026, 2, 5, 12, 0, 0, tzinfo=timezone.utc)
    data = {
        "id": "c-abc1234",
        "text": "Test claim",
        "status": "confirmed",
        "source": "human",
        "author": "metaist",
        "level": "block",
        "tags": ["testing"],
        "verify": {"k-pytest.exit_code": {"eq": 0}},
        "evidence": ["pyproject.toml:5"],
        "created": dt,
        "updated": dt,
        "why": "Because reasons",
        "considered": ["alt1", "alt2"],
        "traces_to": ["c-other"],
        "supersedes": "c-old",
        "closes": ["i-xxx"],
    }
    claim = Claim.parse(data)
    assert claim.id == "c-abc1234"
    assert claim.text == "Test claim"
    assert claim.status == "confirmed"
    assert claim.source == "human"
    assert claim.author == "metaist"
    assert claim.level == "block"
    assert claim.tags == ["testing"]
    assert claim.verify is not None
    assert claim.verify.rules == {"k-pytest.exit_code": {"eq": 0}}
    assert claim.evidence == ["pyproject.toml:5"]
    assert claim.created == dt
    assert claim.updated == dt
    assert claim.why == "Because reasons"
    assert claim.considered == ["alt1", "alt2"]
    assert claim.traces_to == ["c-other"]
    assert claim.supersedes == "c-old"
    assert claim.closes == ["i-xxx"]


def test_claim_to_toml() -> None:
    """Test claim TOML serialization."""
    claim = Claim(
        id="c-abc1234",
        text="Test claim",
        status="confirmed",
        source="human",
        author="tester",
        level="block",
        tags=["foo", "bar"],
        why="Because",
    )
    result = claim.to_toml()
    assert "[[certo.claims]]" in result
    assert 'id = "c-abc1234"' in result
    assert 'text = "Test claim"' in result
    assert 'status = "confirmed"' in result
    assert 'level = "block"' in result
    assert "['foo', 'bar']" in result
    assert 'why = "Because"' in result


def test_claim_to_toml_all_fields() -> None:
    """Test claim TOML serialization with all optional fields."""
    from certo.probe.verify import Verify

    dt = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)
    claim = Claim(
        id="c-abc1234",
        text="Test claim",
        status="confirmed",
        source="human",
        author="tester",
        level="block",
        tags=["foo"],
        verify=Verify.parse({"k-pytest.exit_code": {"eq": 0}}),
        evidence=["proof.txt"],
        created=dt,
        updated=dt,
        why="Because",
        considered=["alt1", "alt2"],
        traces_to=["c-parent"],
        supersedes="c-old",
        closes=["i-xxx"],
    )
    result = claim.to_toml()
    assert "[certo.claims.verify]" in result
    assert "k-pytest.exit_code" in result
    assert "considered = ['alt1', 'alt2']" in result
    assert "traces_to = ['c-parent']" in result
    assert 'supersedes = "c-old"' in result
    assert "closes = ['i-xxx']" in result
    assert "created = 2026-02-05T12:00:00Z" in result
    assert "updated = 2026-02-05T12:00:00Z" in result


def test_claim_parse_with_verify() -> None:
    """Test parsing a claim with verify field."""
    data = {
        "id": "c-abc1234",
        "text": "Test claim",
        "verify": {"k-pytest.exit_code": {"eq": 0}},
    }
    claim = Claim.parse(data)
    assert claim.verify is not None
    assert claim.verify.rules == {"k-pytest.exit_code": {"eq": 0}}


def test_claim_to_toml_with_verify() -> None:
    """Test claim TOML serialization with verify field."""
    from certo.probe.verify import Verify

    claim = Claim(
        id="c-abc1234",
        text="Test claim",
        verify=Verify.parse({"k-pytest.exit_code": {"eq": 0}}),
    )
    result = claim.to_toml()
    assert "[certo.claims.verify]" in result
    assert "k-pytest.exit_code" in result
