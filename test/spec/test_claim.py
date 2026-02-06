"""Tests for Claim parsing and serialization."""

from __future__ import annotations

from datetime import datetime, timezone

from certo.spec import Claim, Modification


def test_modification_parse() -> None:
    """Test parsing a modification."""
    data = {"action": "relax", "claim": "c-xxx"}
    mod = Modification.parse(data)
    assert mod.action == "relax"
    assert mod.claim == "c-xxx"
    assert mod.level == ""
    assert mod.topic == ""


def test_modification_to_toml_inline() -> None:
    """Test modification inline TOML serialization."""
    mod = Modification(action="relax", claim="c-xxx")
    result = mod.to_toml_inline()
    assert 'action = "relax"' in result
    assert 'claim = "c-xxx"' in result

    mod2 = Modification(action="promote", level="warn")
    result2 = mod2.to_toml_inline()
    assert 'level = "warn"' in result2

    mod3 = Modification(action="promote", topic="security")
    result3 = mod3.to_toml_inline()
    assert 'topic = "security"' in result3


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
    assert claim.checks == []
    assert claim.evidence == []
    assert claim.why == ""
    assert claim.considered == []
    assert claim.traces_to == []
    assert claim.supersedes == ""
    assert claim.closes == []


def test_claim_parse_full() -> None:
    """Test parsing a claim with all fields."""
    from certo.check import LLMCheck, ShellCheck

    dt = datetime(2026, 2, 5, 12, 0, 0, tzinfo=timezone.utc)
    data = {
        "id": "c-abc1234",
        "text": "Test claim",
        "status": "confirmed",
        "source": "human",
        "author": "metaist",
        "level": "block",
        "tags": ["testing"],
        "checks": [
            {"kind": "shell", "cmd": "echo test"},
            {"kind": "llm", "files": ["README.md"]},
        ],
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
    assert len(claim.checks) == 2
    assert isinstance(claim.checks[0], ShellCheck)
    assert claim.checks[0].cmd == "echo test"
    assert isinstance(claim.checks[1], LLMCheck)
    assert claim.checks[1].files == ["README.md"]
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
    assert "[[claims]]" in result
    assert 'id = "c-abc1234"' in result
    assert 'text = "Test claim"' in result
    assert 'status = "confirmed"' in result
    assert 'level = "block"' in result
    assert "['foo', 'bar']" in result
    assert 'why = "Because"' in result


def test_claim_to_toml_all_fields() -> None:
    """Test claim TOML serialization with all optional fields."""
    from certo.check import LLMCheck, ShellCheck

    dt = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)
    claim = Claim(
        id="c-abc1234",
        text="Test claim",
        status="confirmed",
        source="human",
        author="tester",
        level="block",
        tags=["foo"],
        checks=[
            ShellCheck(cmd="echo test", matches=["test"]),
            LLMCheck(files=["README.md"]),
        ],
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
    assert "[[claims.checks]]" in result
    assert 'kind = "shell"' in result
    assert 'cmd = "echo test"' in result
    assert 'kind = "llm"' in result
    assert "files = ['README.md']" in result
    assert "considered = ['alt1', 'alt2']" in result
    assert "traces_to = ['c-parent']" in result
    assert 'supersedes = "c-old"' in result
    assert "closes = ['i-xxx']" in result
    assert "created = 2026-02-05T12:00:00Z" in result
    assert "updated = 2026-02-05T12:00:00Z" in result
