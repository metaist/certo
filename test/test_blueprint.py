"""Tests for certo.blueprint module."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from certo.blueprint import Blueprint, Concern, Context, Decision


def test_decision_parse_minimal() -> None:
    """Test parsing a decision with minimal fields."""
    data = {"id": "d1", "title": "Test decision"}
    decision = Decision.parse(data)
    assert decision.id == "d1"
    assert decision.title == "Test decision"
    assert decision.status == "proposed"
    assert decision.description == ""
    assert decision.alternatives == []
    assert decision.rationale == ""
    assert decision.decided_by == ""
    assert decision.decided_on is None


def test_decision_parse_full() -> None:
    """Test parsing a decision with all fields."""
    dt = datetime(2026, 2, 5, 12, 0, 0, tzinfo=timezone.utc)
    data = {
        "id": "d1",
        "title": "Test decision",
        "status": "confirmed",
        "description": "A test decision",
        "alternatives": ["alt1", "alt2"],
        "rationale": "Because reasons",
        "decided_by": "metaist",
        "decided_on": dt,
    }
    decision = Decision.parse(data)
    assert decision.id == "d1"
    assert decision.title == "Test decision"
    assert decision.status == "confirmed"
    assert decision.description == "A test decision"
    assert decision.alternatives == ["alt1", "alt2"]
    assert decision.rationale == "Because reasons"
    assert decision.decided_by == "metaist"
    assert decision.decided_on == dt


def test_concern_parse_minimal() -> None:
    """Test parsing a concern with minimal fields."""
    data = {"id": "c1", "claim": "Something is true"}
    concern = Concern.parse(data)
    assert concern.id == "c1"
    assert concern.claim == "Something is true"
    assert concern.category == ""
    assert concern.strategy == "auto"
    assert concern.context == []
    assert concern.verify_with == []
    assert concern.conditions == []
    assert concern.failure == "warn"
    assert concern.traces_to == []


def test_concern_parse_full() -> None:
    """Test parsing a concern with all fields."""
    data = {
        "id": "c1",
        "claim": "Something is true",
        "category": "functional",
        "strategy": "llm",
        "context": ["README.md"],
        "verify_with": ["test"],
        "conditions": ["condition1"],
        "failure": "block-commit",
        "traces_to": ["d1"],
    }
    concern = Concern.parse(data)
    assert concern.id == "c1"
    assert concern.claim == "Something is true"
    assert concern.category == "functional"
    assert concern.strategy == "llm"
    assert concern.context == ["README.md"]
    assert concern.verify_with == ["test"]
    assert concern.conditions == ["condition1"]
    assert concern.failure == "block-commit"
    assert concern.traces_to == ["d1"]


def test_context_parse_minimal() -> None:
    """Test parsing a context with minimal fields."""
    data = {"id": "ctx1", "name": "Test context"}
    context = Context.parse(data)
    assert context.id == "ctx1"
    assert context.name == "Test context"
    assert context.description == ""
    assert context.applies_to == []
    assert context.expires is None
    assert context.overrides == {}


def test_context_parse_full() -> None:
    """Test parsing a context with all fields."""
    dt = datetime(2026, 12, 31, tzinfo=timezone.utc)
    data = {
        "id": "ctx1",
        "name": "Test context",
        "description": "A test context",
        "applies_to": ["c1", "c2"],
        "expires": dt,
        "overrides": {"strategy": "static"},
    }
    context = Context.parse(data)
    assert context.id == "ctx1"
    assert context.name == "Test context"
    assert context.description == "A test context"
    assert context.applies_to == ["c1", "c2"]
    assert context.expires == dt
    assert context.overrides == {"strategy": "static"}


def test_blueprint_parse_minimal() -> None:
    """Test parsing a blueprint with minimal fields."""
    data = {"blueprint": {"name": "test"}}
    blueprint = Blueprint.parse(data)
    assert blueprint.name == "test"
    assert blueprint.version == ""
    assert blueprint.created is None
    assert blueprint.author == ""
    assert blueprint.description == ""
    assert blueprint.decisions == []
    assert blueprint.concerns == []
    assert blueprint.contexts == []


def test_blueprint_parse_full() -> None:
    """Test parsing a blueprint with all fields."""
    dt = datetime(2026, 2, 5, tzinfo=timezone.utc)
    data = {
        "blueprint": {
            "name": "test",
            "version": "1.0.0",
            "created": dt,
            "author": "metaist",
            "description": "A test blueprint",
        },
        "decisions": [{"id": "d1", "title": "Decision 1"}],
        "concerns": [{"id": "c1", "claim": "Claim 1"}],
        "contexts": [{"id": "ctx1", "name": "Context 1"}],
    }
    blueprint = Blueprint.parse(data)
    assert blueprint.name == "test"
    assert blueprint.version == "1.0.0"
    assert blueprint.created == dt
    assert blueprint.author == "metaist"
    assert blueprint.description == "A test blueprint"
    assert len(blueprint.decisions) == 1
    assert blueprint.decisions[0].id == "d1"
    assert len(blueprint.concerns) == 1
    assert blueprint.concerns[0].id == "c1"
    assert len(blueprint.contexts) == 1
    assert blueprint.contexts[0].id == "ctx1"


def test_blueprint_load() -> None:
    """Test loading a blueprint from a file."""
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "blueprint.toml"
        path.write_text("""
[blueprint]
name = "test"
version = "1.0.0"

[[decisions]]
id = "d1"
title = "Test decision"

[[concerns]]
id = "c1"
claim = "Test claim"
""")
        blueprint = Blueprint.load(path)
        assert blueprint.name == "test"
        assert blueprint.version == "1.0.0"
        assert len(blueprint.decisions) == 1
        assert len(blueprint.concerns) == 1


def test_blueprint_get_concern() -> None:
    """Test getting a concern by ID."""
    data = {
        "blueprint": {"name": "test"},
        "concerns": [
            {"id": "c1", "claim": "Claim 1"},
            {"id": "c2", "claim": "Claim 2"},
        ],
    }
    blueprint = Blueprint.parse(data)
    c1 = blueprint.get_concern("c1")
    assert c1 is not None
    assert c1.claim == "Claim 1"
    assert blueprint.get_concern("c2") is not None
    assert blueprint.get_concern("c3") is None


def test_blueprint_get_decision() -> None:
    """Test getting a decision by ID."""
    data = {
        "blueprint": {"name": "test"},
        "decisions": [
            {"id": "d1", "title": "Decision 1"},
            {"id": "d2", "title": "Decision 2"},
        ],
    }
    blueprint = Blueprint.parse(data)
    d1 = blueprint.get_decision("d1")
    assert d1 is not None
    assert d1.title == "Decision 1"
    assert blueprint.get_decision("d2") is not None
    assert blueprint.get_decision("d3") is None


def test_blueprint_get_context() -> None:
    """Test getting a context by ID."""
    data = {
        "blueprint": {"name": "test"},
        "contexts": [
            {"id": "ctx1", "name": "Context 1"},
            {"id": "ctx2", "name": "Context 2"},
        ],
    }
    blueprint = Blueprint.parse(data)
    ctx1 = blueprint.get_context("ctx1")
    assert ctx1 is not None
    assert ctx1.name == "Context 1"
    assert blueprint.get_context("ctx2") is not None
    assert blueprint.get_context("ctx3") is None
