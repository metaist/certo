"""Tests for certo init command."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from certo.cli import main
from certo.config import CACHE_DIRNAME, CONFIG_FILENAME

if TYPE_CHECKING:
    from pytest import CaptureFixture


def test_init_creates_directory_structure(capsys: CaptureFixture[str]) -> None:
    """Test init creates certo.toml and .certo_cache directory structure."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        result = main(["init", "--path", tmpdir])
        assert result == 0

        # Check directory structure
        assert (root / CONFIG_FILENAME).is_file()
        cache_dir = root / CACHE_DIRNAME
        assert cache_dir.is_dir()
        assert (cache_dir / ".gitignore").is_file()


def test_init_cache_gitignore_contents(capsys: CaptureFixture[str]) -> None:
    """Test cache .gitignore ignores everything."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        main(["init", "--path", tmpdir])

        gitignore = root / CACHE_DIRNAME / ".gitignore"
        contents = gitignore.read_text()
        assert "*" in contents


def test_init_spec_contents(capsys: CaptureFixture[str]) -> None:
    """Test init creates valid spec."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        main(["init", "--path", tmpdir])

        config_path = root / CONFIG_FILENAME
        contents = config_path.read_text()
        assert "version = 1" in contents
