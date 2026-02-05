"""Tests for certo.kb.update module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from certo.kb.update import (
    fetch_url,
    get_latest_commit,
    update_source,
)


def test_fetch_url_mock() -> None:
    """Test fetch_url with mocked response."""
    mock_response = MagicMock()
    mock_response.read.return_value = b"test content"
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = fetch_url("https://example.com")
        assert result == "test content"


def test_get_latest_commit_mock() -> None:
    """Test get_latest_commit with mocked response."""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"sha": "abc123def456"}'
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = get_latest_commit("https://github.com/owner/repo")
        assert result == "abc123def456"


def test_update_source_no_meta() -> None:
    """Test update_source with missing meta.toml."""
    with TemporaryDirectory() as tmpdir:
        result = update_source(Path(tmpdir))
        assert result is False


def test_update_source_mock() -> None:
    """Test update_source with mocked network calls."""
    with TemporaryDirectory() as tmpdir:
        source_path = Path(tmpdir)

        # Create meta.toml
        meta_content = """
[source]
name = "test-source"
url = "https://github.com/test/repo"
commit = "oldcommit"
updated_at = 2026-01-01T00:00:00Z
license = "MIT"
files = ["test.txt"]
"""
        (source_path / "meta.toml").write_text(meta_content)

        # Mock network calls
        def mock_fetch(url: str) -> str:
            if "api.github.com" in url:
                return '{"sha": "newcommit123"}'
            return "fetched file content"

        with patch("certo.kb.update.fetch_url", side_effect=mock_fetch):
            result = update_source(source_path, verbose=True)

        assert result is True

        # Check that files were created
        assert (source_path / "test.txt").exists()
        assert (source_path / "test.txt").read_text() == "fetched file content"

        # Check that meta.toml was updated
        new_meta = (source_path / "meta.toml").read_text()
        assert "newcommit123" in new_meta


def test_update_source_not_verbose() -> None:
    """Test update_source without verbose output."""
    with TemporaryDirectory() as tmpdir:
        source_path = Path(tmpdir)

        meta_content = """
[source]
name = "test-source"
url = "https://github.com/test/repo"
commit = "oldcommit"
updated_at = 2026-01-01T00:00:00Z
license = "MIT"
files = ["test.txt"]
"""
        (source_path / "meta.toml").write_text(meta_content)

        def mock_fetch(url: str) -> str:
            if "api.github.com" in url:
                return '{"sha": "newcommit123"}'
            return "content"

        with patch("certo.kb.update.fetch_url", side_effect=mock_fetch):
            result = update_source(source_path, verbose=False)

        assert result is True


def test_get_kb_path() -> None:
    """Test get_kb_path returns a path."""
    from certo.kb.update import get_kb_path

    path = get_kb_path()
    assert isinstance(path, Path)
    assert "kb" in str(path)


def test_update_all_mock() -> None:
    """Test update_all with mocked sources."""
    from certo.kb.update import update_all

    # This will use the actual kb path and find the real meta.toml
    # We need to mock update_source to avoid network calls
    with patch("certo.kb.update.update_source", return_value=True):
        count = update_all(verbose=False)
        # Should find at least the typeshed source
        assert count >= 1


def test_update_all_source_fails() -> None:
    """Test update_all when update_source returns False."""
    from certo.kb.update import update_all

    with patch("certo.kb.update.update_source", return_value=False):
        count = update_all(verbose=False)
        # Should find sources but none succeed
        assert count == 0


def test_update_python_mock() -> None:
    """Test update_python with mocked update_source."""
    from certo.kb.update import update_python

    with patch("certo.kb.update.update_source", return_value=True):
        result = update_python(verbose=True)
        assert result is True


def test_update_python_missing_path() -> None:
    """Test update_python when path doesn't exist."""
    from certo.kb.update import update_python

    # Mock get_kb_path to return a non-existent path
    with patch("certo.kb.update.get_kb_path", return_value=Path("/nonexistent")):
        result = update_python(verbose=False)
        assert result is False
