"""Tests for check parsing and serialization in spec context."""

from __future__ import annotations

import pytest

from certo.probe import FactCheck, LLMCheck, ShellCheck, parse_check


def test_shell_check_parse() -> None:
    """Test parsing a shell check."""
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
    data = {"kind": "shell"}
    check = ShellCheck.parse(data)
    assert check.cmd == ""
    assert check.exit_code == 0
    assert check.matches == []
    assert check.not_matches == []
    assert check.timeout == 60


def test_shell_check_parse_with_id() -> None:
    """Test parsing a shell check with explicit ID."""
    data = {
        "kind": "shell",
        "id": "k-custom-id",
        "cmd": "echo test",
    }
    check = ShellCheck.parse(data)
    assert check.id == "k-custom-id"


def test_shell_check_auto_generates_id() -> None:
    """Test that shell check auto-generates ID from cmd."""
    data = {
        "kind": "shell",
        "cmd": "echo hello",
    }
    check = ShellCheck.parse(data)
    assert check.id.startswith("k-")
    assert len(check.id) > 2


def test_shell_check_to_toml() -> None:
    """Test shell check TOML serialization."""
    check = ShellCheck(
        cmd="echo test",
        exit_code=1,
        matches=["test"],
        not_matches=["error"],
        timeout=30,
    )
    result = check.to_toml()
    assert "[[probes]]" in result
    assert 'kind = "shell"' in result
    assert 'cmd = "echo test"' in result
    assert "exit_code = 1" in result
    assert "matches = ['test']" in result
    assert "not_matches = ['error']" in result
    assert "timeout = 30" in result


def test_shell_check_to_toml_defaults() -> None:
    """Test shell check TOML serialization with defaults."""
    check = ShellCheck(cmd="echo test")
    result = check.to_toml()
    assert "exit_code" not in result
    assert "matches" not in result
    assert "not_matches" not in result
    assert "timeout" not in result


def test_shell_check_disabled_to_toml() -> None:
    """Test serializing a disabled shell check to TOML."""
    check = ShellCheck(
        id="k-test",
        status="disabled",
        cmd="echo test",
    )
    toml = check.to_toml()
    assert 'status = "disabled"' in toml


def test_llm_check_parse() -> None:
    """Test parsing an LLM check."""
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
    data = {"kind": "llm"}
    check = LLMCheck.parse(data)
    assert check.files == []
    assert check.prompt is None


def test_llm_check_parse_with_id() -> None:
    """Test parsing an LLM check with explicit ID."""
    data = {
        "kind": "llm",
        "id": "k-llm-custom",
        "files": ["README.md"],
    }
    check = LLMCheck.parse(data)
    assert check.id == "k-llm-custom"


def test_llm_check_auto_generates_id() -> None:
    """Test that LLM check auto-generates ID from files."""
    data = {
        "kind": "llm",
        "files": ["src/*.py"],
    }
    check = LLMCheck.parse(data)
    assert check.id.startswith("k-")
    assert len(check.id) > 2


def test_llm_check_to_toml() -> None:
    """Test LLM check TOML serialization."""
    check = LLMCheck(files=["README.md"], prompt="Check X")
    result = check.to_toml()
    assert "[[probes]]" in result
    assert 'kind = "llm"' in result
    assert "files = ['README.md']" in result
    assert 'prompt = "Check X"' in result


def test_llm_check_to_toml_defaults() -> None:
    """Test LLM check TOML serialization with defaults."""
    check = LLMCheck()
    result = check.to_toml()
    assert "files" not in result
    assert "prompt" not in result


def test_llm_check_disabled_to_toml() -> None:
    """Test serializing a disabled LLM check to TOML."""
    check = LLMCheck(
        id="k-test",
        status="disabled",
        files=["README.md"],
    )
    toml = check.to_toml()
    assert 'status = "disabled"' in toml


def test_fact_check_parse() -> None:
    """Test parsing a fact check."""
    data = {
        "kind": "fact",
        "has": "uses.uv",
    }
    check = FactCheck.parse(data)
    assert check.kind == "scan"
    assert check.has == "uses.uv"
    assert check.id.startswith("k-")


def test_fact_check_parse_equals() -> None:
    """Test parsing a fact check with equals."""
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
    check = FactCheck(
        id="k-test",
        has="uses.uv",
    )
    toml = check.to_toml()
    assert 'kind = "scan"' in toml
    assert 'id = "k-test"' in toml
    assert 'has = "uses.uv"' in toml


def test_fact_check_to_toml_disabled() -> None:
    """Test serializing a disabled fact check."""
    check = FactCheck(
        id="k-test",
        status="disabled",
        has="uses.uv",
    )
    toml = check.to_toml()
    assert 'status = "disabled"' in toml


def test_fact_check_to_toml_equals() -> None:
    """Test serializing a fact check with equals."""
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
    check = FactCheck(
        id="k-test",
        matches="python.requires-python",
        pattern=r">=3\.\d+",
    )
    toml = check.to_toml()
    assert 'matches = "python.requires-python"' in toml
    assert 'pattern = ">=3' in toml


def test_parse_check_shell() -> None:
    """Test parse_check dispatches to ShellCheck."""
    data = {"kind": "shell", "cmd": "echo test"}
    check = parse_check(data)
    assert isinstance(check, ShellCheck)
    assert check.cmd == "echo test"


def test_parse_check_llm() -> None:
    """Test parse_check dispatches to LLMCheck."""
    data = {"kind": "llm", "files": ["README.md"]}
    check = parse_check(data)
    assert isinstance(check, LLMCheck)
    assert check.files == ["README.md"]


def test_parse_check_fact() -> None:
    """Test parse_check with fact kind."""
    data = {"kind": "fact", "has": "uses.uv"}
    check = parse_check(data)
    assert isinstance(check, FactCheck)


def test_parse_check_unknown() -> None:
    """Test parse_check raises on unknown kind."""
    data = {"kind": "unknown"}
    with pytest.raises(ValueError, match="Unknown probe kind"):
        parse_check(data)
