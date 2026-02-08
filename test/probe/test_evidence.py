"""Tests for fact types."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from certo.probe.core import Fact
from certo.probe.fact import ScanFact
from certo.probe.llm import LLMFact
from certo.probe.shell import ShellFact
from certo.probe.url import UrlFact


@pytest.fixture
def now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


# Base Fact tests


def test_fact_to_dict_no_timestamp() -> None:
    """Test to_dict with no timestamp."""
    fact = Fact(
        probe_id="k-test",
        kind="custom",
        timestamp=None,
        duration=1.0,
    )
    d = fact.to_dict()
    assert d["timestamp"] == ""


def test_fact_save_load(now: datetime) -> None:
    """Test saving and loading base Fact."""
    fact = Fact(
        probe_id="k-test",
        kind="custom",
        timestamp=now,
        duration=1.0,
    )
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "k-test.json"
        fact.save(path)

        loaded = Fact.load(path)
        assert loaded.probe_id == "k-test"
        assert loaded.kind == "custom"


# ShellFact tests


def test_shell_fact_to_dict(now: datetime) -> None:
    """Test ShellFact.to_dict."""
    fact = ShellFact(
        probe_id="k-pytest",
        kind="shell",
        timestamp=now,
        duration=7.2,
        exit_code=0,
        stdout="411 passed",
        stderr="",
        json={"coverage": 100},
    )
    d = fact.to_dict()
    assert d["probe_id"] == "k-pytest"
    assert d["kind"] == "shell"
    assert d["exit_code"] == 0
    assert d["stdout"] == "411 passed"
    assert d["json"] == {"coverage": 100}


def test_shell_fact_to_dict_no_json(now: datetime) -> None:
    """Test ShellFact.to_dict without JSON."""
    fact = ShellFact(
        probe_id="k-ruff",
        kind="shell",
        timestamp=now,
        duration=0.3,
        exit_code=0,
        stdout="",
        stderr="",
    )
    d = fact.to_dict()
    assert "json" not in d


def test_shell_fact_from_dict(now: datetime) -> None:
    """Test ShellFact.from_dict."""
    data = {
        "probe_id": "k-pytest",
        "kind": "shell",
        "timestamp": now.isoformat(),
        "duration": 7.2,
        "exit_code": 0,
        "stdout": "passed",
        "stderr": "",
        "json": {"foo": "bar"},
    }
    fact = ShellFact.from_dict(data)
    assert fact.probe_id == "k-pytest"
    assert fact.exit_code == 0
    assert fact.json == {"foo": "bar"}


def test_shell_fact_save_load(now: datetime) -> None:
    """Test saving and loading ShellFact."""
    fact = ShellFact(
        probe_id="k-pytest",
        kind="shell",
        timestamp=now,
        duration=7.2,
        probe_hash="abc123",
        exit_code=0,
        stdout="passed",
        stderr="",
    )
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "k-pytest.json"
        fact.save(path)

        loaded = ShellFact.load(path)
        assert loaded.probe_id == "k-pytest"
        assert loaded.exit_code == 0
        assert loaded.probe_hash == "abc123"


# UrlFact tests


def test_url_fact_to_dict(now: datetime) -> None:
    """Test UrlFact.to_dict."""
    fact = UrlFact(
        probe_id="k-eol",
        kind="url",
        timestamp=now,
        duration=0.5,
        status_code=200,
        body='{"versions": []}',
        json={"versions": []},
    )
    d = fact.to_dict()
    assert d["status_code"] == 200
    assert d["body"] == '{"versions": []}'
    assert d["json"] == {"versions": []}


def test_url_fact_from_dict(now: datetime) -> None:
    """Test UrlFact.from_dict."""
    data = {
        "probe_id": "k-eol",
        "kind": "url",
        "timestamp": now.isoformat(),
        "duration": 0.5,
        "status_code": 404,
        "body": "Not found",
    }
    fact = UrlFact.from_dict(data)
    assert fact.status_code == 404
    assert fact.json is None


def test_url_fact_save_load(now: datetime) -> None:
    """Test saving and loading UrlFact."""
    fact = UrlFact(
        probe_id="k-eol",
        kind="url",
        timestamp=now,
        duration=0.5,
        status_code=200,
        body="{}",
    )
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "k-eol.json"
        fact.save(path)

        loaded = UrlFact.load(path)
        assert loaded.status_code == 200


# LLMFact tests


def test_llm_fact_to_dict(now: datetime) -> None:
    """Test LLMFact.to_dict."""
    fact = LLMFact(
        probe_id="k-review",
        kind="llm",
        timestamp=now,
        duration=2.1,
        verdict=True,
        reasoning="Code looks good",
        model="claude-3-opus",
        tokens={"input": 1500, "output": 200},
    )
    d = fact.to_dict()
    assert d["verdict"] is True
    assert d["reasoning"] == "Code looks good"
    assert d["model"] == "claude-3-opus"
    assert d["tokens"]["input"] == 1500


def test_llm_fact_from_dict(now: datetime) -> None:
    """Test LLMFact.from_dict."""
    data = {
        "probe_id": "k-review",
        "kind": "llm",
        "timestamp": now.isoformat(),
        "duration": 2.1,
        "verdict": False,
        "reasoning": "Issue found",
        "model": "gpt-4",
        "tokens": {"input": 1000, "output": 100},
    }
    fact = LLMFact.from_dict(data)
    assert fact.verdict is False
    assert fact.model == "gpt-4"


def test_llm_fact_save_load(now: datetime) -> None:
    """Test saving and loading LLMFact."""
    fact = LLMFact(
        probe_id="k-review",
        kind="llm",
        timestamp=now,
        duration=2.0,
        verdict=True,
        reasoning="OK",
        model="test",
        tokens={},
    )
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "k-review.json"
        fact.save(path)

        loaded = LLMFact.load(path)
        assert loaded.verdict is True


# ScanFact tests


def test_scan_fact_to_dict(now: datetime) -> None:
    """Test ScanFact.to_dict."""
    fact = ScanFact(
        probe_id="k-scan",
        kind="scan",
        timestamp=now,
        duration=0.5,
        facts={
            "python.min-version": "3.11",
            "python.ci-versions": ["3.11", "3.12"],
        },
    )
    d = fact.to_dict()
    assert d["facts"]["python.min-version"] == "3.11"


def test_scan_fact_from_dict(now: datetime) -> None:
    """Test ScanFact.from_dict."""
    data = {
        "probe_id": "k-scan",
        "kind": "scan",
        "timestamp": now.isoformat(),
        "duration": 0.5,
        "facts": {"foo": "bar"},
    }
    fact = ScanFact.from_dict(data)
    assert fact.facts["foo"] == "bar"


def test_scan_fact_save_load(now: datetime) -> None:
    """Test saving and loading ScanFact."""
    fact = ScanFact(
        probe_id="k-scan",
        kind="scan",
        timestamp=now,
        duration=0.5,
        facts={"key": "value"},
    )
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "k-scan.json"
        fact.save(path)

        loaded = ScanFact.load(path)
        assert loaded.facts["key"] == "value"
