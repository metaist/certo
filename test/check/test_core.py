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
        assert len(results) == 1
        assert results[0].passed


def test_check_spec_missing() -> None:
    """Test full check on missing spec."""
    results = check_spec(Path("/nonexistent/.certo/spec.toml"))
    assert len(results) == 1
    assert not results[0].passed


def test_check_spec_skips_static_claims() -> None:
    """Test that static claims without handlers are skipped."""
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
id = "c-static"
text = "Some static check"
status = "confirmed"
verify = ["static"]
""")

        results = check_spec(spec)
        # Should only have builtin (TOML valid), not the static claim
        assert len(results) == 1
        assert results[0].claim_id == "builtin-spec-valid"


def test_check_spec_auto_strategy_with_files() -> None:
    """Test auto strategy with files uses LLM."""
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
verify = ["auto"]
files = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        # Auto with files should try LLM, but offline so skipped
        results = check_spec(spec, offline=True)
        assert len(results) == 2
        assert results[1].claim_id == "c-test"
        assert "skipped" in results[1].message.lower()


def test_check_spec_auto_strategy_without_files() -> None:
    """Test auto strategy without files is skipped."""
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
id = "c-auto-no-files"
text = "Test claim without files"
status = "confirmed"
verify = ["auto"]
""")

        # Auto without files should be silently skipped
        results = check_spec(spec)
        # Should only have builtin (TOML valid), not the auto claim
        assert len(results) == 1
        assert results[0].claim_id == "builtin-spec-valid"


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
verify = ["llm"]
files = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        results = check_spec(spec)
        # Should only have builtin, not the rejected claim
        assert len(results) == 1
        assert results[0].claim_id == "builtin-spec-valid"


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
verify = ["llm"]
files = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        results = check_spec(spec)
        # Should only have builtin, not the skipped claim
        assert len(results) == 1
        assert results[0].claim_id == "builtin-spec-valid"
