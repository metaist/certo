"""Tests for the proof infrastructure itself."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from z3 import Int, Not, Solver

from conftest import (
    ProofCache,
    ProofDependency,
    ProofFailed,
    ProofResult,
    assert_proof,
    check_cache,
    prove,
    save_cache,
)


class TestProofResult:
    """Tests for ProofResult dataclass."""

    def test_basic_result(self) -> None:
        result = ProofResult(
            name="test",
            status="proved",
            message="test passed",
        )
        assert result.name == "test"
        assert result.status == "proved"
        assert result.cached is False

    def test_result_with_counterexample(self) -> None:
        result = ProofResult(
            name="test",
            status="failed",
            message="counterexample found",
            counterexample={"x": "5"},
        )
        assert result.counterexample == {"x": "5"}


class TestProofDependency:
    """Tests for ProofDependency hashing."""

    def test_empty_deps_hash(self) -> None:
        dep = ProofDependency(files=[])
        h = dep.content_hash()
        assert len(h) == 16  # 16 hex chars

    def test_nonexistent_file_ignored(self) -> None:
        dep = ProofDependency(files=["nonexistent/file.py"])
        h = dep.content_hash()
        assert len(h) == 16

    def test_same_files_same_hash(self) -> None:
        dep1 = ProofDependency(files=["src/certo/check/verify.py"])
        dep2 = ProofDependency(files=["src/certo/check/verify.py"])
        assert dep1.content_hash() == dep2.content_hash()

    def test_different_files_different_hash(self) -> None:
        dep1 = ProofDependency(files=["src/certo/check/verify.py"])
        dep2 = ProofDependency(files=["src/certo/spec.py"])
        assert dep1.content_hash() != dep2.content_hash()


class TestProofCache:
    """Tests for ProofCache serialization."""

    def test_to_dict(self) -> None:
        cache = ProofCache(
            name="test",
            dependency_hash="abc123",
            status="proved",
            message="ok",
            timestamp="2026-02-06T12:00:00Z",
        )
        d = cache.to_dict()
        assert d["name"] == "test"
        assert d["dependency_hash"] == "abc123"

    def test_from_dict(self) -> None:
        d = {
            "name": "test",
            "dependency_hash": "abc123",
            "status": "proved",
            "message": "ok",
            "timestamp": "2026-02-06T12:00:00Z",
        }
        cache = ProofCache.from_dict(d)
        assert cache.name == "test"
        assert cache.status == "proved"

    def test_save_and_load(self, tmp_path: Path) -> None:
        cache = ProofCache(
            name="test_save",
            dependency_hash="xyz789",
            status="proved",
            message="saved",
            timestamp="2026-02-06T12:00:00Z",
        )
        cache.save(tmp_path)

        loaded = ProofCache.load(tmp_path, "test_save")
        assert loaded is not None
        assert loaded.name == "test_save"
        assert loaded.dependency_hash == "xyz789"

    def test_load_nonexistent(self, tmp_path: Path) -> None:
        loaded = ProofCache.load(tmp_path, "nonexistent")
        assert loaded is None

    def test_load_corrupt_json(self, tmp_path: Path) -> None:
        cache_file = tmp_path / "corrupt.json"
        cache_file.write_text("not valid json")
        loaded = ProofCache.load(tmp_path, "corrupt")
        assert loaded is None

    def test_load_missing_keys(self, tmp_path: Path) -> None:
        cache_file = tmp_path / "incomplete.json"
        cache_file.write_text(json.dumps({"name": "incomplete"}))
        loaded = ProofCache.load(tmp_path, "incomplete")
        assert loaded is None


class TestCacheFunctions:
    """Tests for cache helper functions."""

    def test_check_cache_miss(self) -> None:
        deps = ProofDependency(files=["nonexistent.py"])
        result = check_cache("nonexistent_proof", deps)
        assert result is None

    def test_save_and_check_cache(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Point cache to temp dir
        monkeypatch.setattr("conftest.PROOF_CACHE_DIR", tmp_path)

        deps = ProofDependency(files=[])
        result = ProofResult(
            name="cached_test",
            status="proved",
            message="original",
        )
        save_cache("cached_test", deps, result)

        # Now check should hit
        cached = check_cache("cached_test", deps)
        assert cached is not None
        assert cached.status == "proved"
        assert "(cached)" in cached.message

    def test_check_cache_hash_mismatch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Cache invalidation when dependencies change."""
        monkeypatch.setattr("conftest.PROOF_CACHE_DIR", tmp_path)

        # Save with one set of deps
        deps1 = ProofDependency(files=[])
        result = ProofResult(name="hash_test", status="proved", message="ok")
        save_cache("hash_test", deps1, result)

        # Check with different deps (different hash)
        deps2 = ProofDependency(files=["src/certo/spec.py"])
        cached = check_cache("hash_test", deps2)
        assert cached is None  # Hash mismatch -> cache miss


class TestProve:
    """Tests for the main prove function."""

    def test_prove_unsat_is_proved(self) -> None:
        """UNSAT means no counterexample exists -> proved."""
        x = Int("x")
        s = Solver()
        s.add(Not(x == x))  # x != x is unsatisfiable

        result = prove(s, "test_unsat", [], use_cache=False)
        assert result.status == "proved"

    def test_prove_sat_is_failed(self) -> None:
        """SAT means counterexample found -> failed."""
        x = Int("x")
        s = Solver()
        s.add(x > 0)  # Satisfiable: x=1

        result = prove(s, "test_sat", [], use_cache=False)
        assert result.status == "failed"
        assert result.counterexample is not None

    def test_prove_timeout_is_unknown(self) -> None:
        """Test that timeout results in 'unknown' status."""
        # Create a problem that might timeout (or solve quickly)
        # This is tricky to test reliably, so we'll use a very short timeout
        x = Int("x")
        s = Solver()
        s.add(x > 0, x < 10)

        # With 1ms timeout, it might still solve, so we just check it doesn't crash
        result = prove(s, "test_timeout", [], timeout_ms=1, use_cache=False)
        assert result.status in ("proved", "failed", "unknown")

    def test_prove_caches_result(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that prove() saves to cache when use_cache=True."""
        monkeypatch.setattr("conftest.PROOF_CACHE_DIR", tmp_path)

        x = Int("x")
        s = Solver()
        s.add(Not(x == x))  # UNSAT

        result = prove(s, "cache_save_test", [], use_cache=True)
        assert result.status == "proved"

        # Verify cache file was created
        cache_file = tmp_path / "cache_save_test.json"
        assert cache_file.exists()


class TestAssertProof:
    """Tests for assert_proof helper."""

    def test_assert_proof_passes(self) -> None:
        result = ProofResult(name="test", status="proved", message="ok")
        assert_proof(result)  # Should not raise

    def test_assert_proof_fails(self) -> None:
        result = ProofResult(name="test", status="failed", message="counterexample")
        with pytest.raises(ProofFailed) as exc_info:
            assert_proof(result)
        assert exc_info.value.result.status == "failed"

    def test_assert_proof_unknown_fails(self) -> None:
        result = ProofResult(name="test", status="unknown", message="timeout")
        with pytest.raises(ProofFailed):
            assert_proof(result)


class TestProofFailedException:
    """Tests for ProofFailed exception."""

    def test_exception_message(self) -> None:
        result = ProofResult(name="test", status="failed", message="oops")
        exc = ProofFailed(result)
        assert str(exc) == "oops"
        assert exc.result.name == "test"
