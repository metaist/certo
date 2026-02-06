"""Tests for certo.check.core module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.check import check_spec


def test_check_spec_integration() -> None:
    """Test full spec check integration."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text('[spec]\nname = "test"\nversion = 1\n')

        results = check_spec(spec)
        # Empty spec = no claims = no results
        assert len(results) == 0


def test_check_spec_missing() -> None:
    """Test full check on missing spec."""
    import pytest

    with pytest.raises(FileNotFoundError):
        check_spec(Path("/nonexistent/.certo/spec.toml"))


def test_check_spec_claims_without_checks_are_skipped() -> None:
    """Test that claims without checks are marked as skipped."""
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
id = "c-no-checks"
text = "Claim with no checks"
status = "confirmed"
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].claim_id == "c-no-checks"
        assert results[0].passed  # Not a failure, just skipped
        assert results[0].skipped
        assert results[0].skip_reason == "no checks defined"
        assert results[0].kind == "none"


def test_check_spec_shell_check() -> None:
    """Test shell check runs command."""
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
id = "c-shell"
text = "Echo works"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "echo hello"
matches = ["hello"]
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].claim_id == "c-shell"
        assert results[0].passed
        assert results[0].kind == "shell"


def test_check_spec_llm_check_offline() -> None:
    """Test LLM check is skipped in offline mode."""
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
id = "c-llm"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "llm"
files = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        results = check_spec(spec, offline=True)
        assert len(results) == 1
        assert results[0].claim_id == "c-llm"
        assert results[0].passed  # Skipped is not a failure
        assert "skipped" in results[0].message.lower()


def test_check_spec_skips_rejected_claims() -> None:
    """Test that rejected claims are skipped."""
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
id = "c-rejected"
text = "Rejected claim"
status = "rejected"

[[claims.checks]]
kind = "shell"
cmd = "false"
""")

        results = check_spec(spec)
        # Should have skipped rejected claim
        assert len(results) == 1
        assert results[0].claim_id == "c-rejected"
        assert results[0].skipped
        assert results[0].skip_reason == "status=rejected"


def test_check_spec_skips_level_skip() -> None:
    """Test that claims with level=skip are skipped."""
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
id = "c-skipped"
text = "Skipped claim"
status = "confirmed"
level = "skip"

[[claims.checks]]
kind = "shell"
cmd = "false"
""")

        results = check_spec(spec)
        # Should have skipped claim
        assert len(results) == 1
        assert results[0].claim_id == "c-skipped"
        assert results[0].skipped
        assert results[0].skip_reason == "level=skip"


def test_check_spec_skip_by_check_id() -> None:
    """Test skipping specific check by ID."""
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
kind = "shell"
id = "k-skip-this"
cmd = "exit 1"

[[claims.checks]]
kind = "shell"
id = "k-run-this"
cmd = "echo hello"
""")

        results = check_spec(spec, skip={"k-skip-this"})
        # Should have builtin + one shell check (the one that wasn't skipped)
        shell_results = [r for r in results if r.kind == "shell"]
        assert len(shell_results) == 1
        assert shell_results[0].check_id == "k-run-this"
        assert shell_results[0].passed


def test_check_spec_only_by_check_id() -> None:
    """Test running only specific check by ID."""
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
kind = "shell"
id = "k-only-this"
cmd = "echo hello"

[[claims.checks]]
kind = "shell"
id = "k-not-this"
cmd = "exit 1"
""")

        results = check_spec(spec, only={"k-only-this"})
        shell_results = [r for r in results if r.kind == "shell"]
        assert len(shell_results) == 1
        assert shell_results[0].check_id == "k-only-this"
        assert shell_results[0].passed


def test_check_spec_skip_builtin() -> None:
    """Test skipping the builtin spec check."""
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
kind = "shell"
cmd = "echo hello"
""")

        results = check_spec(spec, skip={"builtin-spec-valid"})
        # Should not have builtin result
        builtin_results = [r for r in results if r.claim_id == "builtin-spec-valid"]
        assert len(builtin_results) == 0
        # But should still have the shell check
        shell_results = [r for r in results if r.kind == "shell"]
        assert len(shell_results) == 1


def test_check_base_parse_raises() -> None:
    """Test that Check.parse raises NotImplementedError."""
    import pytest
    from certo.check.core import Check

    with pytest.raises(NotImplementedError):
        Check.parse({})


def test_check_base_to_toml_raises() -> None:
    """Test that Check.to_toml raises NotImplementedError."""
    import pytest
    from certo.check.core import Check

    check = Check()
    with pytest.raises(NotImplementedError):
        check.to_toml()
