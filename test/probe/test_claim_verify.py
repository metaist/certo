"""Tests for claim verification against check evidence."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.probe import check_spec


def test_claim_verify_passes() -> None:
    """Test that a claim with verify passes when check passes."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
cmd = "echo hello"

[[claims]]
id = "c-test"
text = "Test passes"
status = "confirmed"

[claims.verify]
"k-test.passed" = { eq = true }
""")

        results = check_spec(spec)

        # Should have 2 results: check result + claim verify result
        assert len(results) == 2

        # Check passed
        check_result = [r for r in results if r.probe_id == "k-test"][0]
        assert check_result.passed

        # Claim verified
        claim_result = [r for r in results if r.rule_id == "c-test"][0]
        assert claim_result.passed
        assert claim_result.kind == "verify"


def test_claim_verify_fails_when_check_fails() -> None:
    """Test that a claim with verify fails when check fails."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[checks]]
id = "k-fail"
kind = "shell"
cmd = "exit 1"

[[claims]]
id = "c-test"
text = "Test requires passing check"
status = "confirmed"

[claims.verify]
"k-fail.passed" = { eq = true }
""")

        results = check_spec(spec)

        # Check failed
        check_result = [r for r in results if r.probe_id == "k-fail"][0]
        assert not check_result.passed

        # Claim verification failed
        claim_result = [r for r in results if r.rule_id == "c-test"][0]
        assert not claim_result.passed


def test_claim_verify_missing_check() -> None:
    """Test that a claim fails when referenced check doesn't exist."""
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
text = "Test references missing check"
status = "confirmed"

[claims.verify]
"k-missing.passed" = { eq = true }
""")

        results = check_spec(spec)

        # Claim verification failed due to missing evidence
        claim_result = [r for r in results if r.rule_id == "c-test"][0]
        assert not claim_result.passed
        # Message could be "missing evidence" or "Verification failed"
        assert not claim_result.passed


def test_claim_without_verify_skipped() -> None:
    """Test that claims without verify are skipped."""
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
text = "Test without verify"
status = "confirmed"
""")

        results = check_spec(spec)

        # Claim should be skipped
        claim_result = [r for r in results if r.rule_id == "c-test"][0]
        assert claim_result.skipped
        assert "no verify" in claim_result.skip_reason.lower()


def test_claim_verify_with_output_match() -> None:
    """Test verifying check output with match operator."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[checks]]
id = "k-hello"
kind = "shell"
cmd = "echo hello world"

[[claims]]
id = "c-test"
text = "Output contains hello"
status = "confirmed"

[claims.verify]
"k-hello.output" = { match = "hello" }
""")

        results = check_spec(spec)

        # Claim should pass
        claim_result = [r for r in results if r.rule_id == "c-test"][0]
        assert claim_result.passed


def test_claim_verify_multiple_conditions() -> None:
    """Test verifying with multiple conditions (implicit AND)."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text("""
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
cmd = "echo hello"

[[claims]]
id = "c-test"
text = "Check passes and has output"
status = "confirmed"

[claims.verify]
"k-test.passed" = { eq = true }
"k-test.skipped" = { eq = false }
""")

        results = check_spec(spec)

        # Claim should pass (both conditions met)
        claim_result = [r for r in results if r.rule_id == "c-test"][0]
        assert claim_result.passed
