"""Tests for certo.spec module."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from certo.spec import (
    Claim,
    Context,
    Issue,
    Modification,
    Spec,
    format_datetime,
    generate_id,
    now_utc,
)


def test_generate_id() -> None:
    """Test ID generation."""
    id1 = generate_id("c", "Test claim one")
    id2 = generate_id("c", "Test claim two")
    id3 = generate_id("c", "Test claim one")  # Same text as id1
    assert id1.startswith("c-")
    assert id2.startswith("c-")
    assert len(id1) == 9  # c- + 7 hex chars
    # Different text = different ID
    assert id1 != id2
    # Same text = same ID (content-addressable)
    assert id1 == id3


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


def test_now_utc() -> None:
    """Test now_utc returns UTC datetime."""
    dt = now_utc()
    assert dt.tzinfo is not None
    offset = dt.tzinfo.utcoffset(dt)
    assert offset is not None
    assert offset.total_seconds() == 0


def test_format_datetime() -> None:
    """Test datetime formatting."""
    dt = datetime(2026, 2, 5, 12, 30, 45, tzinfo=timezone.utc)
    assert format_datetime(dt) == "2026-02-05T12:30:45Z"
    assert format_datetime(None) == ""


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


def test_issue_to_toml() -> None:
    """Test issue TOML serialization."""
    issue = Issue(
        id="i-abc1234",
        text="Test issue",
        status="closed",
        tags=["arch"],
        closed_reason="Done",
    )
    result = issue.to_toml()
    assert "[[issues]]" in result
    assert 'id = "i-abc1234"' in result
    assert 'status = "closed"' in result
    assert 'closed_reason = "Done"' in result


def test_context_to_toml() -> None:
    """Test context TOML serialization."""
    context = Context(
        id="x-abc1234",
        name="release",
        description="For releases",
        modifications=[Modification(action="relax", claim="c-xxx")],
    )
    result = context.to_toml()
    assert "[[contexts]]" in result
    assert 'id = "x-abc1234"' in result
    assert 'name = "release"' in result
    assert "modifications = [" in result


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


def test_issue_to_toml_with_timestamps() -> None:
    """Test issue TOML serialization with timestamps."""
    dt = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)
    issue = Issue(
        id="i-abc1234",
        text="Test issue",
        status="open",
        created=dt,
        updated=dt,
    )
    result = issue.to_toml()
    assert "created = 2026-02-05T12:00:00Z" in result
    assert "updated = 2026-02-05T12:00:00Z" in result


def test_context_to_toml_with_timestamps() -> None:
    """Test context TOML serialization with timestamps."""
    dt = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)
    expires = datetime(2026, 12, 31, tzinfo=timezone.utc)
    context = Context(
        id="x-abc1234",
        name="release",
        created=dt,
        updated=dt,
        expires=expires,
    )
    result = context.to_toml()
    assert "created = 2026-02-05T12:00:00Z" in result
    assert "updated = 2026-02-05T12:00:00Z" in result
    assert "expires = 2026-12-31T00:00:00Z" in result


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


def test_shell_check_parse() -> None:
    """Test parsing a shell check."""
    from certo.check import ShellCheck

    data = {
        "kind": "shell",
        "cmd": "echo test",
        "exit_code": 1,
        "matches": ["test"],
        "not_matches": ["error"],
        "timeout": 30,
    }
    check = ShellCheck.parse(data)
    assert check.kind == "shell"
    assert check.cmd == "echo test"
    assert check.exit_code == 1
    assert check.matches == ["test"]
    assert check.not_matches == ["error"]
    assert check.timeout == 30


def test_shell_check_parse_defaults() -> None:
    """Test parsing a shell check with defaults."""
    from certo.check import ShellCheck

    data = {"kind": "shell"}
    check = ShellCheck.parse(data)
    assert check.cmd == ""
    assert check.exit_code == 0
    assert check.matches == []
    assert check.not_matches == []
    assert check.timeout == 60


def test_shell_check_to_toml() -> None:
    """Test shell check TOML serialization."""
    from certo.check import ShellCheck

    check = ShellCheck(
        cmd="echo test",
        exit_code=1,
        matches=["test"],
        not_matches=["error"],
        timeout=30,
    )
    result = check.to_toml()
    assert "[[claims.checks]]" in result
    assert 'kind = "shell"' in result
    assert 'cmd = "echo test"' in result
    assert "exit_code = 1" in result
    assert "matches = ['test']" in result
    assert "not_matches = ['error']" in result
    assert "timeout = 30" in result


def test_shell_check_to_toml_defaults() -> None:
    """Test shell check TOML serialization with defaults."""
    from certo.check import ShellCheck

    check = ShellCheck(cmd="echo test")
    result = check.to_toml()
    assert "exit_code" not in result
    assert "matches" not in result
    assert "not_matches" not in result
    assert "timeout" not in result


def test_llm_check_parse() -> None:
    """Test parsing an LLM check."""
    from certo.check import LLMCheck

    data = {
        "kind": "llm",
        "files": ["README.md", "src/*.py"],
        "prompt": "Check for X",
    }
    check = LLMCheck.parse(data)
    assert check.kind == "llm"
    assert check.files == ["README.md", "src/*.py"]
    assert check.prompt == "Check for X"


def test_llm_check_parse_defaults() -> None:
    """Test parsing an LLM check with defaults."""
    from certo.check import LLMCheck

    data = {"kind": "llm"}
    check = LLMCheck.parse(data)
    assert check.files == []
    assert check.prompt is None


def test_llm_check_to_toml() -> None:
    """Test LLM check TOML serialization."""
    from certo.check import LLMCheck

    check = LLMCheck(files=["README.md"], prompt="Check X")
    result = check.to_toml()
    assert "[[claims.checks]]" in result
    assert 'kind = "llm"' in result
    assert "files = ['README.md']" in result
    assert 'prompt = "Check X"' in result


def test_llm_check_to_toml_defaults() -> None:
    """Test LLM check TOML serialization with defaults."""
    from certo.check import LLMCheck

    check = LLMCheck()
    result = check.to_toml()
    assert "files" not in result
    assert "prompt" not in result


def test_parse_check_shell() -> None:
    """Test parse_check dispatches to ShellCheck."""
    from certo.check import ShellCheck, parse_check

    data = {"kind": "shell", "cmd": "echo test"}
    check = parse_check(data)
    assert isinstance(check, ShellCheck)
    assert check.cmd == "echo test"


def test_parse_check_llm() -> None:
    """Test parse_check dispatches to LLMCheck."""
    from certo.check import LLMCheck, parse_check

    data = {"kind": "llm", "files": ["README.md"]}
    check = parse_check(data)
    assert isinstance(check, LLMCheck)
    assert check.files == ["README.md"]


def test_parse_check_unknown() -> None:
    """Test parse_check raises on unknown kind."""
    from certo.check import parse_check
    import pytest

    data = {"kind": "unknown"}
    with pytest.raises(ValueError, match="Unknown check kind"):
        parse_check(data)


def test_shell_check_parse_with_id() -> None:
    """Test parsing a shell check with explicit ID."""
    from certo.check import ShellCheck

    data = {
        "kind": "shell",
        "id": "k-custom-id",
        "cmd": "echo test",
    }
    check = ShellCheck.parse(data)
    assert check.id == "k-custom-id"


def test_shell_check_auto_generates_id() -> None:
    """Test that shell check auto-generates ID from cmd."""
    from certo.check import ShellCheck

    data = {
        "kind": "shell",
        "cmd": "echo hello",
    }
    check = ShellCheck.parse(data)
    assert check.id.startswith("k-")
    assert len(check.id) > 2


def test_llm_check_parse_with_id() -> None:
    """Test parsing an LLM check with explicit ID."""
    from certo.check import LLMCheck

    data = {
        "kind": "llm",
        "id": "k-llm-custom",
        "files": ["README.md"],
    }
    check = LLMCheck.parse(data)
    assert check.id == "k-llm-custom"


def test_llm_check_auto_generates_id() -> None:
    """Test that LLM check auto-generates ID from files."""
    from certo.check import LLMCheck

    data = {
        "kind": "llm",
        "files": ["src/*.py"],
    }
    check = LLMCheck.parse(data)
    assert check.id.startswith("k-")
    assert len(check.id) > 2


def test_shell_check_disabled_to_toml() -> None:
    """Test serializing a disabled shell check to TOML."""
    from certo.check import ShellCheck

    check = ShellCheck(
        id="k-test",
        status="disabled",
        cmd="echo test",
    )
    toml = check.to_toml()
    assert 'status = "disabled"' in toml


def test_llm_check_disabled_to_toml() -> None:
    """Test serializing a disabled LLM check to TOML."""
    from certo.check import LLMCheck

    check = LLMCheck(
        id="k-test",
        status="disabled",
        files=["README.md"],
    )
    toml = check.to_toml()
    assert 'status = "disabled"' in toml


def test_fact_check_parse() -> None:
    """Test parsing a fact check."""
    from certo.check import FactCheck

    data = {
        "kind": "fact",
        "has": "uses.uv",
    }
    check = FactCheck.parse(data)
    assert check.kind == "fact"
    assert check.has == "uses.uv"
    assert check.id.startswith("k-")


def test_fact_check_parse_equals() -> None:
    """Test parsing a fact check with equals."""
    from certo.check import FactCheck

    data = {
        "kind": "fact",
        "id": "k-custom",
        "equals": "python.min-version",
        "value": "3.11",
    }
    check = FactCheck.parse(data)
    assert check.id == "k-custom"
    assert check.equals == "python.min-version"
    assert check.value == "3.11"


def test_fact_check_parse_matches() -> None:
    """Test parsing a fact check with matches."""
    from certo.check import FactCheck

    data = {
        "kind": "fact",
        "matches": "python.requires-python",
        "pattern": r">=3\.\d+",
    }
    check = FactCheck.parse(data)
    assert check.matches == "python.requires-python"
    assert check.pattern == r">=3\.\d+"


def test_fact_check_to_toml() -> None:
    """Test serializing a fact check to TOML."""
    from certo.check import FactCheck

    check = FactCheck(
        id="k-test",
        has="uses.uv",
    )
    toml = check.to_toml()
    assert 'kind = "fact"' in toml
    assert 'id = "k-test"' in toml
    assert 'has = "uses.uv"' in toml


def test_fact_check_to_toml_disabled() -> None:
    """Test serializing a disabled fact check."""
    from certo.check import FactCheck

    check = FactCheck(
        id="k-test",
        status="disabled",
        has="uses.uv",
    )
    toml = check.to_toml()
    assert 'status = "disabled"' in toml


def test_fact_check_to_toml_equals() -> None:
    """Test serializing a fact check with equals."""
    from certo.check import FactCheck

    check = FactCheck(
        id="k-test",
        equals="python.min-version",
        value="3.11",
    )
    toml = check.to_toml()
    assert 'equals = "python.min-version"' in toml
    assert 'value = "3.11"' in toml


def test_fact_check_to_toml_matches() -> None:
    """Test serializing a fact check with matches."""
    from certo.check import FactCheck

    check = FactCheck(
        id="k-test",
        matches="python.requires-python",
        pattern=r">=3\.\d+",
    )
    toml = check.to_toml()
    assert 'matches = "python.requires-python"' in toml
    assert 'pattern = ">=3' in toml


def test_parse_check_fact() -> None:
    """Test parse_check with fact kind."""
    from certo.check import FactCheck, parse_check

    data = {"kind": "fact", "has": "uses.uv"}
    check = parse_check(data)
    assert isinstance(check, FactCheck)
