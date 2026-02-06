"""Tests for evidence types."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from certo.check.core import Evidence
from certo.check.fact import FactEvidence
from certo.check.llm import LlmEvidence
from certo.check.shell import ShellEvidence
from certo.check.url import UrlEvidence


@pytest.fixture
def now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


# Base Evidence tests


def test_evidence_to_dict_no_timestamp() -> None:
    """Test to_dict with no timestamp."""
    evidence = Evidence(
        check_id="k-test",
        kind="custom",
        timestamp=None,
        duration=1.0,
    )
    d = evidence.to_dict()
    assert d["timestamp"] == ""


def test_evidence_save_load(now: datetime) -> None:
    """Test saving and loading base Evidence."""
    evidence = Evidence(
        check_id="k-test",
        kind="custom",
        timestamp=now,
        duration=1.0,
    )
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "k-test.json"
        evidence.save(path)

        loaded = Evidence.load(path)
        assert loaded.check_id == "k-test"
        assert loaded.kind == "custom"


# ShellEvidence tests


def test_shell_evidence_to_dict(now: datetime) -> None:
    """Test ShellEvidence.to_dict."""
    evidence = ShellEvidence(
        check_id="k-pytest",
        kind="shell",
        timestamp=now,
        duration=7.2,
        exit_code=0,
        stdout="411 passed",
        stderr="",
        json={"coverage": 100},
    )
    d = evidence.to_dict()
    assert d["check_id"] == "k-pytest"
    assert d["kind"] == "shell"
    assert d["exit_code"] == 0
    assert d["stdout"] == "411 passed"
    assert d["json"] == {"coverage": 100}


def test_shell_evidence_to_dict_no_json(now: datetime) -> None:
    """Test ShellEvidence.to_dict without JSON."""
    evidence = ShellEvidence(
        check_id="k-ruff",
        kind="shell",
        timestamp=now,
        duration=0.3,
        exit_code=0,
        stdout="",
        stderr="",
    )
    d = evidence.to_dict()
    assert "json" not in d


def test_shell_evidence_from_dict(now: datetime) -> None:
    """Test ShellEvidence.from_dict."""
    data = {
        "check_id": "k-pytest",
        "kind": "shell",
        "timestamp": now.isoformat(),
        "duration": 7.2,
        "exit_code": 0,
        "stdout": "passed",
        "stderr": "",
        "json": {"foo": "bar"},
    }
    evidence = ShellEvidence.from_dict(data)
    assert evidence.check_id == "k-pytest"
    assert evidence.exit_code == 0
    assert evidence.json == {"foo": "bar"}


def test_shell_evidence_save_load(now: datetime) -> None:
    """Test saving and loading ShellEvidence."""
    evidence = ShellEvidence(
        check_id="k-pytest",
        kind="shell",
        timestamp=now,
        duration=7.2,
        check_hash="abc123",
        exit_code=0,
        stdout="passed",
        stderr="",
    )
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "k-pytest.json"
        evidence.save(path)

        loaded = ShellEvidence.load(path)
        assert loaded.check_id == "k-pytest"
        assert loaded.exit_code == 0
        assert loaded.check_hash == "abc123"


# UrlEvidence tests


def test_url_evidence_to_dict(now: datetime) -> None:
    """Test UrlEvidence.to_dict."""
    evidence = UrlEvidence(
        check_id="k-eol",
        kind="url",
        timestamp=now,
        duration=0.5,
        status_code=200,
        body='{"versions": []}',
        json={"versions": []},
    )
    d = evidence.to_dict()
    assert d["status_code"] == 200
    assert d["body"] == '{"versions": []}'
    assert d["json"] == {"versions": []}


def test_url_evidence_from_dict(now: datetime) -> None:
    """Test UrlEvidence.from_dict."""
    data = {
        "check_id": "k-eol",
        "kind": "url",
        "timestamp": now.isoformat(),
        "duration": 0.5,
        "status_code": 404,
        "body": "Not found",
    }
    evidence = UrlEvidence.from_dict(data)
    assert evidence.status_code == 404
    assert evidence.json is None


def test_url_evidence_save_load(now: datetime) -> None:
    """Test saving and loading UrlEvidence."""
    evidence = UrlEvidence(
        check_id="k-eol",
        kind="url",
        timestamp=now,
        duration=0.5,
        status_code=200,
        body="{}",
    )
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "k-eol.json"
        evidence.save(path)

        loaded = UrlEvidence.load(path)
        assert loaded.status_code == 200


# LlmEvidence tests


def test_llm_evidence_to_dict(now: datetime) -> None:
    """Test LlmEvidence.to_dict."""
    evidence = LlmEvidence(
        check_id="k-review",
        kind="llm",
        timestamp=now,
        duration=2.1,
        verdict=True,
        reasoning="Code looks good",
        model="claude-3-opus",
        tokens={"input": 1500, "output": 200},
    )
    d = evidence.to_dict()
    assert d["verdict"] is True
    assert d["reasoning"] == "Code looks good"
    assert d["model"] == "claude-3-opus"
    assert d["tokens"]["input"] == 1500


def test_llm_evidence_from_dict(now: datetime) -> None:
    """Test LlmEvidence.from_dict."""
    data = {
        "check_id": "k-review",
        "kind": "llm",
        "timestamp": now.isoformat(),
        "duration": 2.1,
        "verdict": False,
        "reasoning": "Issue found",
        "model": "gpt-4",
        "tokens": {"input": 1000, "output": 100},
    }
    evidence = LlmEvidence.from_dict(data)
    assert evidence.verdict is False
    assert evidence.model == "gpt-4"


def test_llm_evidence_save_load(now: datetime) -> None:
    """Test saving and loading LlmEvidence."""
    evidence = LlmEvidence(
        check_id="k-review",
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
        evidence.save(path)

        loaded = LlmEvidence.load(path)
        assert loaded.verdict is True


# FactEvidence tests


def test_fact_evidence_to_dict(now: datetime) -> None:
    """Test FactEvidence.to_dict."""
    evidence = FactEvidence(
        check_id="k-scan",
        kind="fact",
        timestamp=now,
        duration=0.5,
        facts={
            "python.min-version": "3.11",
            "python.ci-versions": ["3.11", "3.12"],
        },
    )
    d = evidence.to_dict()
    assert d["facts"]["python.min-version"] == "3.11"


def test_fact_evidence_from_dict(now: datetime) -> None:
    """Test FactEvidence.from_dict."""
    data = {
        "check_id": "k-scan",
        "kind": "fact",
        "timestamp": now.isoformat(),
        "duration": 0.5,
        "facts": {"foo": "bar"},
    }
    evidence = FactEvidence.from_dict(data)
    assert evidence.facts["foo"] == "bar"


def test_fact_evidence_save_load(now: datetime) -> None:
    """Test saving and loading FactEvidence."""
    evidence = FactEvidence(
        check_id="k-scan",
        kind="fact",
        timestamp=now,
        duration=0.5,
        facts={"key": "value"},
    )
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "k-scan.json"
        evidence.save(path)

        loaded = FactEvidence.load(path)
        assert loaded.facts["key"] == "value"
