"""Tests for certo.check.url module."""

from __future__ import annotations

import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from certo.check.core import CheckContext
from certo.check.url import UrlCheck, UrlRunner
from certo.spec import Claim


def test_url_check_parse() -> None:
    """Test parsing a URL check."""
    data = {
        "kind": "url",
        "id": "k-test",
        "url": "https://example.com/api.json",
        "cache_ttl": 3600,
        "cmd": "jq .",
    }
    check = UrlCheck.parse(data)
    assert check.kind == "url"
    assert check.id == "k-test"
    assert check.url == "https://example.com/api.json"
    assert check.cache_ttl == 3600
    assert check.cmd == "jq ."


def test_url_check_parse_defaults() -> None:
    """Test parsing a URL check with defaults."""
    data = {"kind": "url", "url": "https://example.com"}
    check = UrlCheck.parse(data)
    assert check.cache_ttl == 86400
    assert check.cmd == ""
    assert check.id.startswith("k-")


def test_url_check_to_toml() -> None:
    """Test URL check serialization."""
    check = UrlCheck(
        id="k-test",
        url="https://example.com/api.json",
        cmd="jq .",
    )
    toml = check.to_toml()
    assert 'id = "k-test"' in toml
    assert 'kind = "url"' in toml
    assert 'url = "https://example.com/api.json"' in toml
    assert 'cmd = "jq ."' in toml


def test_url_check_to_toml_with_cache_ttl() -> None:
    """Test URL check serialization with non-default cache_ttl."""
    check = UrlCheck(
        id="k-test",
        url="https://example.com",
        cache_ttl=3600,
    )
    toml = check.to_toml()
    assert "cache_ttl = 3600" in toml


def test_url_runner_no_url() -> None:
    """Test URL runner with missing URL."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        ctx = CheckContext(
            project_root=root,
            spec_path=root / ".certo" / "spec.toml",
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = UrlCheck(id="k-test", url="")

        result = UrlRunner().run(ctx, claim, check)
        assert not result.passed
        assert "no url" in result.message.lower()


def test_url_runner_offline_no_cache() -> None:
    """Test URL runner in offline mode without cache."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()

        ctx = CheckContext(
            project_root=root,
            spec_path=certo_dir / "spec.toml",
            offline=True,
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = UrlCheck(id="k-test", url="https://example.com")

        result = UrlRunner().run(ctx, claim, check)
        assert result.skipped
        assert "offline" in result.skip_reason.lower()


def test_url_runner_uses_cache() -> None:
    """Test URL runner uses cached response."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        cache_dir = certo_dir / "cache" / "url"
        cache_dir.mkdir(parents=True)

        # Create cached response
        import hashlib

        url = "https://example.com/test.json"
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
        cache_file = cache_dir / f"{url_hash}.txt"
        cache_meta = cache_dir / f"{url_hash}.meta"
        cache_file.write_text('{"status": "ok"}')
        cache_meta.write_text(f"{time.time()}\n{url}")

        ctx = CheckContext(
            project_root=root,
            spec_path=certo_dir / "spec.toml",
            offline=True,
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = UrlCheck(id="k-test", url=url)

        result = UrlRunner().run(ctx, claim, check)
        assert result.passed
        assert "(cached)" in result.message


def test_url_runner_cache_expired() -> None:
    """Test URL runner ignores expired cache."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        cache_dir = certo_dir / "cache" / "url"
        cache_dir.mkdir(parents=True)

        # Create expired cached response
        import hashlib

        url = "https://example.com/test.json"
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
        cache_file = cache_dir / f"{url_hash}.txt"
        cache_meta = cache_dir / f"{url_hash}.meta"
        cache_file.write_text('{"status": "ok"}')
        # Set time to 2 days ago (expired for default 1 day TTL)
        cache_meta.write_text(f"{time.time() - 200000}\n{url}")

        ctx = CheckContext(
            project_root=root,
            spec_path=certo_dir / "spec.toml",
            offline=True,
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = UrlCheck(id="k-test", url=url)

        result = UrlRunner().run(ctx, claim, check)
        # Should skip because cache expired and we're offline
        assert result.skipped


def test_url_runner_fetches_url() -> None:
    """Test URL runner fetches URL when not cached."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()

        ctx = CheckContext(
            project_root=root,
            spec_path=certo_dir / "spec.toml",
            offline=False,
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = UrlCheck(id="k-test", url="https://example.com")

        # Mock urlopen
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"status": "ok"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = UrlRunner().run(ctx, claim, check)

        assert result.passed
        assert "fetched" in result.message.lower()


def test_url_runner_fetch_error() -> None:
    """Test URL runner handles fetch error."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()

        ctx = CheckContext(
            project_root=root,
            spec_path=certo_dir / "spec.toml",
            offline=False,
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = UrlCheck(id="k-test", url="https://example.com")

        with patch("urllib.request.urlopen", side_effect=Exception("Connection error")):
            result = UrlRunner().run(ctx, claim, check)

        assert not result.passed
        assert "failed to fetch" in result.message.lower()


def test_url_runner_with_command() -> None:
    """Test URL runner pipes to shell command."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        cache_dir = certo_dir / "cache" / "url"
        cache_dir.mkdir(parents=True)

        # Create cached response
        import hashlib

        url = "https://example.com/test.json"
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
        cache_file = cache_dir / f"{url_hash}.txt"
        cache_meta = cache_dir / f"{url_hash}.meta"
        cache_file.write_text('{"status": "ok"}')
        cache_meta.write_text(f"{time.time()}\n{url}")

        ctx = CheckContext(
            project_root=root,
            spec_path=certo_dir / "spec.toml",
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = UrlCheck(id="k-test", url=url, cmd="cat")

        result = UrlRunner().run(ctx, claim, check)
        assert result.passed
        assert '{"status": "ok"}' in result.output


def test_url_runner_command_fails() -> None:
    """Test URL runner when shell command fails."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        cache_dir = certo_dir / "cache" / "url"
        cache_dir.mkdir(parents=True)

        # Create cached response
        import hashlib

        url = "https://example.com/test.json"
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
        cache_file = cache_dir / f"{url_hash}.txt"
        cache_meta = cache_dir / f"{url_hash}.meta"
        cache_file.write_text('{"status": "ok"}')
        cache_meta.write_text(f"{time.time()}\n{url}")

        ctx = CheckContext(
            project_root=root,
            spec_path=certo_dir / "spec.toml",
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = UrlCheck(id="k-test", url=url, cmd="false")

        result = UrlRunner().run(ctx, claim, check)
        assert not result.passed
        assert "exit code" in result.message.lower()


def test_url_check_to_toml_all_options() -> None:
    """Test URL check serialization with all options."""
    check = UrlCheck(
        id="k-test",
        status="disabled",
        url="https://example.com/api.json",
        cache_ttl=3600,
        cmd="jq .",
        exit_code=1,
        matches=["ok"],
        not_matches=["error"],
        timeout=30,
    )
    toml = check.to_toml()
    assert 'id = "k-test"' in toml
    assert 'status = "disabled"' in toml
    assert 'url = "https://example.com/api.json"' in toml
    assert "cache_ttl = 3600" in toml
    assert 'cmd = "jq ."' in toml
    assert "exit_code = 1" in toml
    assert "matches = ['ok']" in toml
    assert "not_matches = ['error']" in toml
    assert "timeout = 30" in toml


def test_url_runner_handles_corrupted_cache_meta() -> None:
    """Test URL runner handles corrupted cache metadata."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        cache_dir = certo_dir / "cache" / "url"
        cache_dir.mkdir(parents=True)

        # Create cache with corrupted meta
        import hashlib

        url = "https://example.com/test.json"
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
        cache_file = cache_dir / f"{url_hash}.txt"
        cache_meta = cache_dir / f"{url_hash}.meta"
        cache_file.write_text('{"status": "ok"}')
        cache_meta.write_text("not a valid timestamp\n{url}")  # Corrupted

        ctx = CheckContext(
            project_root=root,
            spec_path=certo_dir / "spec.toml",
            offline=True,
        )
        claim = Claim(id="c-test", text="Test", status="confirmed")
        check = UrlCheck(id="k-test", url=url)

        result = UrlRunner().run(ctx, claim, check)
        # Should skip because cache is corrupted and we're offline
        assert result.skipped
