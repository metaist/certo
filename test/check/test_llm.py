"""Tests for certo.check.llm module."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from certo.check import check_spec


def test_check_spec_with_llm_claim_offline() -> None:
    """Test that LLM claims are skipped in offline mode."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "llm"
files = ["README.md"]
""")
        # Create the context file
        (root / "README.md").write_text("# Test")

        results = check_spec(spec, offline=True)
        # Should have builtin (TOML valid) + c-test (skipped)
        assert len(results) == 1
        assert results[0].claim_id == "c-test"
        assert results[0].passed  # Skipped counts as pass
        assert "skipped" in results[0].message.lower()


def test_check_spec_llm_missing_files() -> None:
    """Test that missing files fail fast."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "llm"
files = ["nonexistent.md"]
""")

        # Not offline, so it will try to verify
        # Missing files should fail before API key check
        results = check_spec(spec, offline=False)
        assert len(results) == 1
        assert results[0].claim_id == "c-test"
        assert not results[0].passed
        assert (
            "missing" in results[0].message.lower()
            or "not found" in results[0].message.lower()
        )


def test_check_spec_llm_missing_text() -> None:
    """Test that claims without text fail."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
status = "confirmed"

[[claims.checks]]
kind = "llm"
files = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        results = check_spec(spec, offline=True)
        assert len(results) == 1
        assert results[0].claim_id == "c-test"
        assert not results[0].passed
        assert "text" in results[0].message.lower()


def test_check_spec_llm_missing_files_field() -> None:
    """Test that LLM checks without files field fail."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "llm"
""")

        results = check_spec(spec, offline=True)
        assert len(results) == 1
        assert results[0].claim_id == "c-test"
        assert not results[0].passed
        assert "files" in results[0].message.lower()


def test_check_spec_llm_no_api_key() -> None:
    """Test that missing API key gives clear error."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "llm"
files = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        # Ensure no API key
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENROUTER_API_KEY", None)
            results = check_spec(spec, offline=False)

        assert len(results) == 1
        assert results[0].claim_id == "c-test"
        assert results[0].skipped
        assert "api key" in results[0].message.lower()


def test_check_spec_llm_file_too_large() -> None:
    """Test that large files give clear error."""
    from certo.llm.verify import MAX_CONTEXT_FILE_SIZE

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "llm"
files = ["large.txt"]
""")
        # Create a file larger than the limit
        (root / "large.txt").write_text("x" * (MAX_CONTEXT_FILE_SIZE + 1))

        results = check_spec(spec, offline=False)
        assert len(results) == 1
        assert results[0].claim_id == "c-test"
        assert not results[0].passed
        assert "too large" in results[0].message.lower()


def test_check_spec_llm_api_error() -> None:
    """Test that API errors give clear message."""
    from certo.llm.provider import APIError

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "llm"
files = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        with patch("certo.llm.verify.call_llm") as mock_call:
            mock_call.side_effect = APIError("Connection failed")
            results = check_spec(spec, offline=False)

        assert len(results) == 1
        assert results[0].claim_id == "c-test"
        assert not results[0].passed
        assert "llm error" in results[0].message.lower()


def test_check_spec_llm_cached_result() -> None:
    """Test that cached results show (cached) in message."""
    from certo.llm.verify import VerificationResult

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "llm"
files = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        mock_result = VerificationResult(
            passed=True,
            explanation="All good",
            model="test-model",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            cost=0.001,
            cached=True,
            cache_key="abc123",
        )

        with patch("certo.llm.verify.verify_concern", return_value=mock_result):
            results = check_spec(spec, offline=False)

        assert len(results) == 1
        assert results[0].claim_id == "c-test"
        assert results[0].passed
        assert "(cached)" in results[0].message
