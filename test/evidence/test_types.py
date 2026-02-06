"""Tests for evidence types."""

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from certo.evidence.types import (
    Evidence,
    ShellEvidence,
    UrlEvidence,
    LlmEvidence,
    FactEvidence,
    load_evidence,
    save_evidence,
)


@pytest.fixture
def now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class TestShellEvidence:
    """Tests for ShellEvidence."""

    def test_to_dict(self, now: datetime) -> None:
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

    def test_to_dict_no_json(self, now: datetime) -> None:
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

    def test_from_dict(self, now: datetime) -> None:
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


class TestUrlEvidence:
    """Tests for UrlEvidence."""

    def test_to_dict(self, now: datetime) -> None:
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

    def test_from_dict(self, now: datetime) -> None:
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


class TestLlmEvidence:
    """Tests for LlmEvidence."""

    def test_to_dict(self, now: datetime) -> None:
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

    def test_from_dict(self, now: datetime) -> None:
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


class TestFactEvidence:
    """Tests for FactEvidence."""

    def test_to_dict(self, now: datetime) -> None:
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

    def test_from_dict(self, now: datetime) -> None:
        data = {
            "check_id": "k-scan",
            "kind": "fact",
            "timestamp": now.isoformat(),
            "duration": 0.5,
            "facts": {"foo": "bar"},
        }
        evidence = FactEvidence.from_dict(data)
        assert evidence.facts["foo"] == "bar"


class TestBaseEvidence:
    """Tests for base Evidence class."""

    def test_to_dict_no_timestamp(self) -> None:
        """Test to_dict with no timestamp."""
        evidence = Evidence(
            check_id="k-test",
            kind="custom",
            timestamp=None,
            duration=1.0,
        )
        d = evidence.to_dict()
        assert d["timestamp"] == ""


class TestEvidenceSaveLoad:
    """Tests for saving and loading evidence."""

    def test_save_load_shell(self, now: datetime) -> None:
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
            path = Path(tmpdir) / "evidence" / "k-pytest.json"
            save_evidence(evidence, path)

            loaded = load_evidence(path)
            assert isinstance(loaded, ShellEvidence)
            assert loaded.check_id == "k-pytest"
            assert loaded.exit_code == 0
            assert loaded.check_hash == "abc123"

    def test_save_load_url(self, now: datetime) -> None:
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
            save_evidence(evidence, path)

            loaded = load_evidence(path)
            assert isinstance(loaded, UrlEvidence)
            assert loaded.status_code == 200

    def test_save_load_llm(self, now: datetime) -> None:
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
            save_evidence(evidence, path)

            loaded = load_evidence(path)
            assert isinstance(loaded, LlmEvidence)
            assert loaded.verdict is True

    def test_save_load_fact(self, now: datetime) -> None:
        evidence = FactEvidence(
            check_id="k-scan",
            kind="fact",
            timestamp=now,
            duration=0.5,
            facts={"key": "value"},
        )
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "k-scan.json"
            save_evidence(evidence, path)

            loaded = load_evidence(path)
            assert isinstance(loaded, FactEvidence)
            assert loaded.facts["key"] == "value"

    def test_load_unknown_kind(self, now: datetime) -> None:
        """Load evidence with unknown kind returns base Evidence."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "k-unknown.json"
            data = {
                "check_id": "k-unknown",
                "kind": "custom",
                "timestamp": now.isoformat(),
                "duration": 1.0,
            }
            path.write_text(json.dumps(data))

            loaded = load_evidence(path)
            assert isinstance(loaded, Evidence)
            assert loaded.kind == "custom"
