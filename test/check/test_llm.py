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


def test_check_spec_llm_offline_invalid_cache() -> None:
    """Test that invalid cached evidence is ignored."""
    from certo.check import check_spec

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
id = "k-test"
files = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        # Create invalid evidence file
        evidence_dir = certo_dir / "evidence"
        evidence_dir.mkdir()
        evidence_file = evidence_dir / "k-test.json"
        evidence_file.write_text("not valid json {{{")

        results = check_spec(spec, offline=True)

        assert len(results) == 1
        assert results[0].skipped  # Falls through to skip
        assert "offline" in results[0].skip_reason.lower()


def test_check_spec_llm_offline_uses_valid_cache() -> None:
    """Test that valid cached evidence is used in offline mode."""
    from certo.check import check_spec

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
id = "k-test"
files = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        # Create valid evidence file
        import json

        evidence_dir = certo_dir / "evidence"
        evidence_dir.mkdir()
        evidence_file = evidence_dir / "k-test.json"
        evidence_file.write_text(
            json.dumps(
                {
                    "passed": True,
                    "message": "Verified by LLM",
                    "reasoning": "The claim is valid",
                }
            )
        )

        results = check_spec(spec, offline=True)

        assert len(results) == 1
        assert results[0].passed
        assert "(cached)" in results[0].message


def test_llm_runner_saves_evidence() -> None:
    """Test LLM runner saves evidence to file."""
    from unittest.mock import patch
    from certo.check.llm import LLMCheck, LLMRunner
    from certo.check.core import CheckContext
    from certo.spec import Claim
    from certo.llm.verify import VerificationResult

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()

        ctx = CheckContext(
            project_root=root,
            spec_path=certo_dir / "spec.toml",
            offline=False,
        )
        claim = Claim(id="c-test", text="Test claim", status="confirmed")
        check = LLMCheck(id="k-test123", files=["README.md"])

        # Create the file
        (root / "README.md").write_text("# Test")

        mock_result = VerificationResult(
            passed=True,
            explanation="Verified",
            model="test-model",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cached=False,
        )

        with patch("certo.llm.verify.verify_concern", return_value=mock_result):
            result = LLMRunner().run(ctx, claim, check)

        assert result.passed
        evidence_file = certo_dir / "evidence" / "k-test123.json"
        assert evidence_file.exists()
        import json

        evidence = json.loads(evidence_file.read_text())
        assert evidence["passed"] is True


def test_llm_runner_uses_claim_id_fallback_for_evidence() -> None:
    """Test LLM runner uses claim.id as evidence filename when check has no ID."""
    from unittest.mock import patch
    from certo.check.llm import LLMCheck, LLMRunner
    from certo.check.core import CheckContext
    from certo.spec import Claim
    from certo.llm.verify import VerificationResult

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()

        ctx = CheckContext(
            project_root=root,
            spec_path=certo_dir / "spec.toml",
            offline=False,
        )
        claim = Claim(id="c-test", text="Test claim", status="confirmed")
        check = LLMCheck(id="", files=["README.md"])  # No ID - falls back to claim.id

        (root / "README.md").write_text("# Test")

        mock_result = VerificationResult(
            passed=True,
            explanation="Verified",
            model="test-model",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cached=False,
        )

        with patch("certo.llm.verify.verify_concern", return_value=mock_result):
            result = LLMRunner().run(ctx, claim, check)

        assert result.passed
        evidence_dir = certo_dir / "evidence"
        # Evidence saved with claim.id as fallback
        evidence_file = evidence_dir / "c-test.json"
        assert evidence_file.exists()


def test_llm_runner_cached_message() -> None:
    """Test LLM runner adds cached indicator to message."""
    from unittest.mock import patch
    from certo.check.llm import LLMCheck, LLMRunner
    from certo.check.core import CheckContext
    from certo.spec import Claim
    from certo.llm.verify import VerificationResult

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()

        ctx = CheckContext(
            project_root=root,
            spec_path=certo_dir / "spec.toml",
            offline=False,
        )
        claim = Claim(id="c-test", text="Test claim", status="confirmed")
        check = LLMCheck(id="k-test", files=["README.md"])

        (root / "README.md").write_text("# Test")

        mock_result = VerificationResult(
            passed=True,
            explanation="Verified",
            model="test-model",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cached=True,  # Cached result
        )

        with patch("certo.llm.verify.verify_concern", return_value=mock_result):
            result = LLMRunner().run(ctx, claim, check)

        assert result.passed
        assert "(cached)" in result.message
