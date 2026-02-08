"""Tests for certo.probe.llm module."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from certo.probe import check_spec


def test_check_spec_with_llm_check_offline() -> None:
    """Test that LLM checks are skipped in offline mode."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config = root / "certo.toml"
        config.write_text("""
[spec]
name = "test"
version = 1

[[probes]]
id = "k-llm"
kind = "llm"
files = ["README.md"]
prompt = "Check this file"
""")
        # Create the context file
        (root / "README.md").write_text("# Test")

        results = check_spec(config, offline=True)
        assert len(results) == 1
        assert results[0].probe_id == "k-llm"
        assert results[0].passed  # Skipped counts as pass
        assert "skipped" in results[0].message.lower()


def test_check_spec_llm_missing_files() -> None:
    """Test that missing files fail fast."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config = root / "certo.toml"
        config.write_text("""
[spec]
name = "test"
version = 1

[[probes]]
id = "k-llm"
kind = "llm"
files = ["nonexistent.md"]
prompt = "Verify this"
""")

        # Not offline, so it will try to verify
        # Missing files should fail before API key check
        results = check_spec(config, offline=False)
        assert len(results) == 1
        assert results[0].probe_id == "k-llm"
        assert not results[0].passed
        assert (
            "missing" in results[0].message.lower()
            or "not found" in results[0].message.lower()
        )


def test_check_spec_llm_missing_files_field() -> None:
    """Test that LLM check without files fails."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config = root / "certo.toml"
        config.write_text("""
[spec]
name = "test"
version = 1

[[probes]]
id = "k-llm"
kind = "llm"
prompt = "Verify something"
""")

        results = check_spec(config, offline=False)
        assert len(results) == 1
        assert results[0].probe_id == "k-llm"
        assert not results[0].passed
        assert "files" in results[0].message.lower()


def test_check_spec_llm_missing_prompt() -> None:
    """Test that LLM check without prompt (and no claim) fails."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config = root / "certo.toml"
        config.write_text("""
[spec]
name = "test"
version = 1

[[probes]]
id = "k-llm"
kind = "llm"
files = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        results = check_spec(config, offline=False)
        assert len(results) == 1
        assert results[0].probe_id == "k-llm"
        assert not results[0].passed
        assert (
            "prompt" in results[0].message.lower()
            or "text" in results[0].message.lower()
        )


def test_check_spec_llm_no_api_key() -> None:
    """Test that LLM check skips without API key."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config = root / "certo.toml"
        config.write_text("""
[spec]
name = "test"
version = 1

[[probes]]
id = "k-llm"
kind = "llm"
files = ["README.md"]
prompt = "Verify this"
""")
        (root / "README.md").write_text("# Test")

        # Ensure no API key is set
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENROUTER_API_KEY", None)
            results = check_spec(config, offline=False)
            assert len(results) == 1
            assert results[0].probe_id == "k-llm"
            # Without API key, should skip
            assert results[0].skipped or not results[0].passed


def test_check_spec_llm_file_too_large() -> None:
    """Test that oversized files fail."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config = root / "certo.toml"
        config.write_text("""
[spec]
name = "test"
version = 1

[[probes]]
id = "k-llm"
kind = "llm"
files = ["bigfile.md"]
prompt = "Verify this"
""")
        # Create a file larger than 100KB
        (root / "bigfile.md").write_text("x" * 200_000)

        results = check_spec(config, offline=False)
        assert len(results) == 1
        assert results[0].probe_id == "k-llm"
        # File too large should fail
        assert not results[0].passed


def test_check_spec_llm_api_error() -> None:
    """Test handling of API errors."""
    from certo.llm.provider import LLMError

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config = root / "certo.toml"
        config.write_text("""
[spec]
name = "test"
version = 1

[[probes]]
id = "k-llm"
kind = "llm"
files = ["README.md"]
prompt = "Verify this"
""")
        (root / "README.md").write_text("# Test")

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            with patch("certo.llm.provider.call_llm") as mock_llm:
                mock_llm.side_effect = LLMError("API Error")
                results = check_spec(config, offline=False)
                assert len(results) == 1
                assert results[0].probe_id == "k-llm"
                assert not results[0].passed
                assert "error" in results[0].message.lower()


def test_check_spec_llm_offline_with_cached_evidence() -> None:
    """Test that offline mode uses cached evidence."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config = root / "certo.toml"
        config.write_text("""
[spec]
name = "test"
version = 1

[[probes]]
id = "k-llm"
kind = "llm"
files = ["README.md"]
prompt = "Verify this"
""")
        (root / "README.md").write_text("# Test")

        # Create evidence file in new cache location
        evidence_dir = root / ".certo_cache" / "evidence"
        evidence_dir.mkdir(parents=True)
        evidence_file = evidence_dir / "k-llm.json"
        evidence_file.write_text(
            json.dumps(
                {
                    "passed": True,
                    "message": "Previously verified",
                    "reasoning": "Looks good",
                }
            )
        )

        results = check_spec(config, offline=True)
        assert len(results) == 1
        assert results[0].probe_id == "k-llm"
        assert results[0].passed
        assert "cached" in results[0].message.lower()
