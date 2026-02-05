"""Tests for certo.llm.verify module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from certo.llm.provider import LLMResponse
from certo.llm.verify import (
    MAX_CONTEXT_FILE_SIZE,
    FileMissingError,
    FileTooLargeError,
    _build_prompt,
    _hash_inputs,
    _load_context,
    _resolve_globs,
    verify_concern,
)


def test_hash_inputs_deterministic() -> None:
    """Test that hash is deterministic."""
    claim = "test claim"
    contents = {"file1.py": "content1", "file2.py": "content2"}

    hash1 = _hash_inputs(claim, contents)
    hash2 = _hash_inputs(claim, contents)
    assert hash1 == hash2


def test_hash_inputs_changes_with_content() -> None:
    """Test that hash changes when content changes."""
    claim = "test claim"
    contents1 = {"file1.py": "content1"}
    contents2 = {"file1.py": "content2"}

    hash1 = _hash_inputs(claim, contents1)
    hash2 = _hash_inputs(claim, contents2)
    assert hash1 != hash2


def test_resolve_globs_literal_file() -> None:
    """Test resolving a literal file path."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "test.py").write_text("content")

        files = _resolve_globs(["test.py"], root)
        assert len(files) == 1
        assert files[0].name == "test.py"


def test_resolve_globs_pattern() -> None:
    """Test resolving glob patterns."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        src.mkdir()
        (src / "a.py").write_text("a")
        (src / "b.py").write_text("b")
        (src / "c.txt").write_text("c")

        files = _resolve_globs(["src/*.py"], root)
        assert len(files) == 2
        names = {f.name for f in files}
        assert names == {"a.py", "b.py"}


def test_resolve_globs_deduplicates() -> None:
    """Test that duplicate files are removed."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "test.py").write_text("content")

        files = _resolve_globs(["test.py", "*.py"], root)
        assert len(files) == 1


def test_load_context_success() -> None:
    """Test loading context files."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "test.py").write_text("test content")

        contents, files = _load_context(["test.py"], root)
        assert "test.py" in contents
        assert contents["test.py"] == "test content"
        assert len(files) == 1


def test_load_context_no_matches() -> None:
    """Test error when no files match."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        with pytest.raises(FileMissingError) as exc_info:
            _load_context(["nonexistent.py"], root)
        assert "no files found" in str(exc_info.value).lower()


def test_load_context_file_too_large() -> None:
    """Test error when file exceeds size limit."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        large_file = root / "large.py"
        # Create a file larger than the limit
        large_file.write_text("x" * (MAX_CONTEXT_FILE_SIZE + 1))

        with pytest.raises(FileTooLargeError) as exc_info:
            _load_context(["large.py"], root)
        assert "exceeds limit" in str(exc_info.value).lower()


def test_load_context_file_deleted_after_glob() -> None:
    """Test error when file is deleted between glob and read."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        nonexistent = root / "deleted.py"

        # Mock _resolve_globs to return a path that doesn't exist
        with patch("certo.llm.verify._resolve_globs", return_value=[nonexistent]):
            with pytest.raises(FileMissingError) as exc_info:
                _load_context(["*.py"], root)
            assert "not found" in str(exc_info.value).lower()


def test_build_prompt() -> None:
    """Test building verification prompt."""
    claim = "Test claim"
    contents = {"test.py": "print('hello')"}

    prompt = _build_prompt(claim, contents)
    assert "Test claim" in prompt
    assert "test.py" in prompt
    assert "print('hello')" in prompt


def test_verify_concern_cached() -> None:
    """Test that cached results are returned."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        cache_dir = certo_dir / "cache"
        cache_dir.mkdir()

        # Create context file
        (root / "test.py").write_text("test content")

        # Create a mock cached result
        # First, get the cache key by computing it
        from certo.llm.verify import _get_cache_path, _hash_inputs

        cache_key = _hash_inputs("Test claim", {"test.py": "test content"})
        cache_path = _get_cache_path(root, cache_key, "c-test")

        cache_path.write_text(f'''
[meta]
concern_id = "c-test"
cache_key = "{cache_key}"
timestamp = "2026-02-05T18:00:00+00:00"
model = "test-model"
prompt_tokens = 100
completion_tokens = 50
total_tokens = 150

[claim]
text = """Test claim"""
context = ["test.py"]

[result]
passed = true
explanation = """Cached result"""
''')

        result = verify_concern(
            concern_id="c-test",
            claim="Test claim",
            context_patterns=["test.py"],
            project_root=root,
        )

        assert result.cached
        assert result.passed
        assert result.explanation == "Cached result"


def test_verify_concern_no_cache() -> None:
    """Test that no_cache skips cache lookup."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()

        (root / "test.py").write_text("test content")

        mock_response = LLMResponse(
            content='{"pass": true, "explanation": "Fresh result"}',
            model="test-model",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            cost=0.001,
        )

        with patch("certo.llm.verify.call_llm", return_value=mock_response):
            result = verify_concern(
                concern_id="c-test",
                claim="Test claim",
                context_patterns=["test.py"],
                project_root=root,
                no_cache=True,
            )

            assert not result.cached
            assert result.passed
            assert result.explanation == "Fresh result"


def test_verify_concern_saves_cache() -> None:
    """Test that results are cached."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()

        (root / "test.py").write_text("test content")

        mock_response = LLMResponse(
            content='{"pass": false, "explanation": "Test failed"}',
            model="test-model",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            cost=0.001,
        )

        with patch("certo.llm.verify.call_llm", return_value=mock_response):
            result = verify_concern(
                concern_id="c-test",
                claim="Test claim",
                context_patterns=["test.py"],
                project_root=root,
            )

            assert not result.passed
            assert result.explanation == "Test failed"

            # Check cache file was created
            cache_dir = certo_dir / "cache"
            cache_files = list(cache_dir.glob("c-test-*.toml"))
            assert len(cache_files) == 1


def test_verify_concern_invalid_json_response() -> None:
    """Test handling of invalid JSON from LLM."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()

        (root / "test.py").write_text("test content")

        mock_response = LLMResponse(
            content="not valid json",
            model="test-model",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            cost=0.001,
        )

        with patch("certo.llm.verify.call_llm", return_value=mock_response):
            result = verify_concern(
                concern_id="c-test",
                claim="Test claim",
                context_patterns=["test.py"],
                project_root=root,
            )

            # Should fail gracefully
            assert not result.passed
            assert "failed to parse" in result.explanation.lower()


def test_load_cached_result_invalid_toml() -> None:
    """Test handling of invalid cache file."""
    from certo.llm.verify import _load_cached_result

    with TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "invalid.toml"
        cache_path.write_text("not valid toml [[[")

        result = _load_cached_result(cache_path)
        assert result is None


def test_load_cached_result_missing_fields() -> None:
    """Test handling of cache file with missing fields."""
    from certo.llm.verify import _load_cached_result

    with TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "incomplete.toml"
        cache_path.write_text('[meta]\ncache_key = "test"\n')

        result = _load_cached_result(cache_path)
        assert result is None


def test_verify_concern_json_regex_match_but_invalid() -> None:
    """Test handling when JSON regex matches but content is invalid."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()

        (root / "test.py").write_text("test content")

        # Response has JSON-like pattern but with invalid escape sequence
        # The regex will match, but json.loads will fail
        mock_response = LLMResponse(
            content='Some text {"pass": true, "explanation": "test\\xinvalid"} more text',
            model="test-model",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            cost=0.001,
        )

        with patch("certo.llm.verify.call_llm", return_value=mock_response):
            result = verify_concern(
                concern_id="c-test",
                claim="Test claim",
                context_patterns=["test.py"],
                project_root=root,
                no_cache=True,
            )

            # Should fail gracefully since JSON is malformed
            assert not result.passed
            assert "failed to parse" in result.explanation.lower()
