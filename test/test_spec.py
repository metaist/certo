"""Tests for certo.spec module."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from certo.spec import Claim, Context, Issue, Modification, Spec, generate_id


def test_generate_id() -> None:
    """Test ID generation."""
    id1 = generate_id("c")
    id2 = generate_id("c")
    assert id1.startswith("c-")
    assert id2.startswith("c-")
    assert len(id1) == 9  # c- + 7 hex chars
    # IDs should be unique (different timestamps)
    assert id1 != id2


def test_modification_parse() -> None:
    """Test parsing a modification."""
    data = {"action": "relax", "claim": "c-xxx"}
    mod = Modification.parse(data)
    assert mod.action == "relax"
    assert mod.claim == "c-xxx"
    assert mod.level == ""
    assert mod.topic == ""


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
    assert claim.verify == []
    assert claim.files == []
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
        "verify": ["static", "llm"],
        "files": ["README.md"],
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
    assert claim.verify == ["static", "llm"]
    assert claim.files == ["README.md"]
    assert claim.evidence == ["pyproject.toml:5"]
    assert claim.created == dt
    assert claim.updated == dt
    assert claim.why == "Because reasons"
    assert claim.considered == ["alt1", "alt2"]
    assert claim.traces_to == ["c-other"]
    assert claim.supersedes == "c-old"
    assert claim.closes == ["i-xxx"]


def test_issue_parse_minimal() -> None:
    """Test parsing an issue with minimal fields."""
    data = {"id": "i-abc1234", "text": "Test issue"}
    issue = Issue.parse(data)
    assert issue.id == "i-abc1234"
    assert issue.text == "Test issue"
    assert issue.status == "open"
    assert issue.tags == []
    assert issue.closed_reason == ""


def test_issue_parse_full() -> None:
    """Test parsing an issue with all fields."""
    dt = datetime(2026, 2, 5, 12, 0, 0, tzinfo=timezone.utc)
    data = {
        "id": "i-abc1234",
        "text": "Test issue",
        "status": "closed",
        "tags": ["architecture"],
        "created": dt,
        "updated": dt,
        "closed_reason": "Resolved by c-xxx",
    }
    issue = Issue.parse(data)
    assert issue.id == "i-abc1234"
    assert issue.text == "Test issue"
    assert issue.status == "closed"
    assert issue.tags == ["architecture"]
    assert issue.created == dt
    assert issue.updated == dt
    assert issue.closed_reason == "Resolved by c-xxx"


def test_context_parse_minimal() -> None:
    """Test parsing a context with minimal fields."""
    data = {"id": "x-abc1234", "name": "Test context"}
    context = Context.parse(data)
    assert context.id == "x-abc1234"
    assert context.name == "Test context"
    assert context.description == ""
    assert context.modifications == []
    assert context.expires is None


def test_context_parse_full() -> None:
    """Test parsing a context with all fields."""
    dt = datetime(2026, 12, 31, tzinfo=timezone.utc)
    data = {
        "id": "x-abc1234",
        "name": "Test context",
        "description": "A test context",
        "created": dt,
        "updated": dt,
        "expires": dt,
        "modifications": [{"action": "relax", "claim": "c-xxx"}],
    }
    context = Context.parse(data)
    assert context.id == "x-abc1234"
    assert context.name == "Test context"
    assert context.description == "A test context"
    assert context.created == dt
    assert context.updated == dt
    assert context.expires == dt
    assert len(context.modifications) == 1
    assert context.modifications[0].action == "relax"


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
