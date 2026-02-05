"""Tests for certo.check module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.check import (
    CheckContext,
    check_blueprint,
    check_blueprint_exists,
    check_blueprint_valid_toml,
)


def _make_ctx(blueprint_path: Path) -> CheckContext:
    """Create a CheckContext for testing."""
    return CheckContext(
        project_root=blueprint_path.parent,
        blueprint_path=blueprint_path,
    )


def test_check_blueprint_exists_success() -> None:
    """Test that existing blueprint is detected."""
    with TemporaryDirectory() as tmpdir:
        blueprint = Path(tmpdir) / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        ctx = _make_ctx(blueprint)
        result = check_blueprint_exists(ctx)
        assert result.passed
        assert result.concern_id == "c1"


def test_check_blueprint_exists_failure() -> None:
    """Test that missing blueprint is detected."""
    ctx = _make_ctx(Path("/nonexistent/blueprint.toml"))
    result = check_blueprint_exists(ctx)
    assert not result.passed
    assert "not found" in result.message.lower()


def test_check_blueprint_valid_toml_success() -> None:
    """Test that valid TOML is accepted."""
    with TemporaryDirectory() as tmpdir:
        blueprint = Path(tmpdir) / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\nversion = "0.1.0"\n')

        ctx = _make_ctx(blueprint)
        result = check_blueprint_valid_toml(ctx)
        assert result.passed
        assert result.strategy == "static"


def test_check_blueprint_valid_toml_failure() -> None:
    """Test that invalid TOML is rejected."""
    with TemporaryDirectory() as tmpdir:
        blueprint = Path(tmpdir) / "blueprint.toml"
        blueprint.write_text("this is not valid toml [[[")

        ctx = _make_ctx(blueprint)
        result = check_blueprint_valid_toml(ctx)
        assert not result.passed
        assert "invalid toml" in result.message.lower()


def test_check_blueprint_valid_toml_missing_file() -> None:
    """Test TOML check on missing file."""
    ctx = _make_ctx(Path("/nonexistent/blueprint.toml"))
    result = check_blueprint_valid_toml(ctx)
    assert not result.passed
    assert "does not exist" in result.message.lower()


def test_check_blueprint_integration() -> None:
    """Test full blueprint check integration."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text('[blueprint]\nname = "test"\n')

        results = check_blueprint(blueprint)
        assert len(results) == 1
        assert results[0].passed


def test_check_blueprint_missing() -> None:
    """Test full check on missing blueprint."""
    results = check_blueprint(Path("/nonexistent/.certo/blueprint.toml"))
    assert len(results) == 1
    assert not results[0].passed


def test_check_blueprint_with_llm_concern_offline() -> None:
    """Test that LLM concerns are skipped in offline mode."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-test"
claim = "Test claim"
strategy = "llm"
context = ["README.md"]
""")
        # Create the context file
        (root / "README.md").write_text("# Test")

        results = check_blueprint(blueprint, offline=True)
        # Should have c1 (TOML valid) + c-test (skipped)
        assert len(results) == 2
        assert results[1].concern_id == "c-test"
        assert results[1].passed  # Skipped counts as pass
        assert "skipped" in results[1].message.lower()


def test_check_blueprint_llm_missing_context() -> None:
    """Test that missing context files fail fast."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-test"
claim = "Test claim"
strategy = "llm"
context = ["nonexistent.md"]
""")

        # Not offline, so it will try to verify
        # But no API key, so it should fail with API key error first
        # Actually, missing files should fail before API key check
        results = check_blueprint(blueprint, offline=False)
        assert len(results) == 2
        assert results[1].concern_id == "c-test"
        assert not results[1].passed
        assert (
            "missing" in results[1].message.lower()
            or "not found" in results[1].message.lower()
        )


def test_check_blueprint_llm_missing_claim() -> None:
    """Test that concerns without claim fail."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-test"
strategy = "llm"
context = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        results = check_blueprint(blueprint, offline=True)
        assert len(results) == 2
        assert results[1].concern_id == "c-test"
        assert not results[1].passed
        assert "claim" in results[1].message.lower()


def test_check_blueprint_llm_missing_context_field() -> None:
    """Test that concerns without context field fail."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-test"
claim = "Test claim"
strategy = "llm"
""")

        results = check_blueprint(blueprint, offline=True)
        assert len(results) == 2
        assert results[1].concern_id == "c-test"
        assert not results[1].passed
        assert "context" in results[1].message.lower()


def test_check_blueprint_llm_no_api_key() -> None:
    """Test that missing API key gives clear error."""
    import os
    from unittest.mock import patch

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-test"
claim = "Test claim"
strategy = "llm"
context = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        # Ensure no API key
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENROUTER_API_KEY", None)
            results = check_blueprint(blueprint, offline=False)

        assert len(results) == 2
        assert results[1].concern_id == "c-test"
        assert not results[1].passed
        assert "api key" in results[1].message.lower()


def test_check_blueprint_llm_file_too_large() -> None:
    """Test that large files give clear error."""
    from certo.llm.verify import MAX_CONTEXT_FILE_SIZE

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-test"
claim = "Test claim"
strategy = "llm"
context = ["large.txt"]
""")
        # Create a file larger than the limit
        (root / "large.txt").write_text("x" * (MAX_CONTEXT_FILE_SIZE + 1))

        results = check_blueprint(blueprint, offline=False)
        assert len(results) == 2
        assert results[1].concern_id == "c-test"
        assert not results[1].passed
        assert "too large" in results[1].message.lower()


def test_check_blueprint_llm_api_error() -> None:
    """Test that API errors give clear message."""
    from unittest.mock import patch

    from certo.llm.provider import APIError

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-test"
claim = "Test claim"
strategy = "llm"
context = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        with patch("certo.llm.verify.call_llm") as mock_call:
            mock_call.side_effect = APIError("Connection failed")
            results = check_blueprint(blueprint, offline=False)

        assert len(results) == 2
        assert results[1].concern_id == "c-test"
        assert not results[1].passed
        assert "llm error" in results[1].message.lower()


def test_check_blueprint_skips_static_concerns() -> None:
    """Test that static concerns without handlers are skipped."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-static"
claim = "Some static check"
strategy = "static"
""")

        results = check_blueprint(blueprint)
        # Should only have c1 (TOML valid), not the static concern
        assert len(results) == 1
        assert results[0].concern_id == "c1"


def test_check_blueprint_auto_strategy_with_context() -> None:
    """Test auto strategy with context uses LLM."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-test"
claim = "Test claim"
strategy = "auto"
context = ["README.md"]
""")
        (root / "README.md").write_text("# Test")

        # Auto with context should try LLM, but offline so skipped
        results = check_blueprint(blueprint, offline=True)
        assert len(results) == 2
        assert results[1].concern_id == "c-test"
        assert "skipped" in results[1].message.lower()


def test_check_blueprint_auto_strategy_without_context() -> None:
    """Test auto strategy without context is skipped."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-auto-no-context"
claim = "Test claim without context"
strategy = "auto"
""")

        # Auto without context should be silently skipped
        results = check_blueprint(blueprint)
        # Should only have c1 (TOML valid), not the auto concern
        assert len(results) == 1
        assert results[0].concern_id == "c1"


def test_check_blueprint_llm_cached_result() -> None:
    """Test that cached results show (cached) in message."""
    from unittest.mock import patch

    from certo.llm.verify import VerificationResult

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "blueprint.toml"
        blueprint.write_text("""
[blueprint]
name = "test"

[[concerns]]
id = "c-test"
claim = "Test claim"
strategy = "llm"
context = ["README.md"]
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
            results = check_blueprint(blueprint, offline=False)

        assert len(results) == 2
        assert results[1].concern_id == "c-test"
        assert results[1].passed
        assert "(cached)" in results[1].message
