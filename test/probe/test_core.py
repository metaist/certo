"""Tests for certo.check.core module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.probe import check_spec


def test_check_spec_integration() -> None:
    """Test full spec check integration."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        spec = certo_dir / "spec.toml"
        spec.write_text('[spec]\nname = "test"\nversion = 1\n')

        results = check_spec(spec)
        # Empty spec = no checks, no claims = no results
        assert len(results) == 0


def test_check_spec_missing() -> None:
    """Test full check on missing spec."""
    import pytest

    with pytest.raises(FileNotFoundError):
        check_spec(Path("/nonexistent/.certo/spec.toml"))


def test_check_spec_claims_without_verify_are_skipped() -> None:
    """Test that claims without verify are marked as skipped."""
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
id = "c-no-verify"
text = "Claim without verify"
status = "confirmed"
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].rule_id == "c-no-verify"
        assert results[0].passed  # Not a failure, just skipped
        assert results[0].skipped
        assert results[0].skip_reason == "no verify defined"
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

[[checks]]
id = "k-shell"
kind = "shell"
cmd = "echo hello"
matches = ["hello"]
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].probe_id == "k-shell"
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

[[checks]]
id = "k-llm"
kind = "llm"
files = ["README.md"]
prompt = "Verify this file"
""")
        (root / "README.md").write_text("# Test")

        results = check_spec(spec, offline=True)
        assert len(results) == 1
        assert results[0].probe_id == "k-llm"
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
""")

        results = check_spec(spec)
        # Should have skipped rejected claim
        assert len(results) == 1
        assert results[0].rule_id == "c-rejected"
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
""")

        results = check_spec(spec)
        # Should have skipped claim
        assert len(results) == 1
        assert results[0].rule_id == "c-skipped"
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

[[checks]]
id = "k-skip-this"
kind = "shell"
cmd = "exit 1"

[[checks]]
id = "k-run-this"
kind = "shell"
cmd = "echo hello"
""")

        results = check_spec(spec, skip={"k-skip-this"})
        shell_results = [r for r in results if r.kind == "shell"]
        assert len(shell_results) == 1
        assert shell_results[0].probe_id == "k-run-this"
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

[[checks]]
id = "k-only-this"
kind = "shell"
cmd = "echo hello"

[[checks]]
id = "k-not-this"
kind = "shell"
cmd = "exit 1"
""")

        results = check_spec(spec, only={"k-only-this"})
        shell_results = [r for r in results if r.kind == "shell"]
        assert len(shell_results) == 1
        assert shell_results[0].probe_id == "k-only-this"
        assert shell_results[0].passed


def test_check_spec_disabled_check() -> None:
    """Test that disabled checks are skipped."""
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
id = "k-disabled"
kind = "shell"
status = "disabled"
cmd = "exit 1"
""")

        results = check_spec(spec)
        assert len(results) == 1
        assert results[0].probe_id == "k-disabled"
        assert results[0].skipped
        assert results[0].skip_reason == "probe disabled"


def test_check_base_parse_raises() -> None:
    """Test that Check.parse raises NotImplementedError."""
    import pytest
    from certo.probe.core import Check

    with pytest.raises(NotImplementedError):
        Check.parse({})


def test_check_base_to_toml_raises() -> None:
    """Test that Check.to_toml raises NotImplementedError."""
    import pytest
    from certo.probe.core import Check

    check = Check()
    with pytest.raises(NotImplementedError):
        check.to_toml()


def test_check_content_hash() -> None:
    """Test Check.content_hash generates deterministic hash."""
    from certo.probe.core import Check

    check = Check(kind="shell", id="k-test")
    hash1 = check.content_hash()
    hash2 = check.content_hash()
    assert hash1 == hash2
    assert hash1.startswith("h-")
