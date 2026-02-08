"""Tests for certo.config module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from certo.config import (
    CONFIG_FILENAME,
    CACHE_DIRNAME,
    find_config,
    get_project_root,
    get_cache_dir,
    ensure_cache_dir,
)


def test_find_config_in_current_dir() -> None:
    """Test finding config in current directory."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config_path = root / CONFIG_FILENAME
        config_path.write_text('[spec]\nname = "test"\n')

        found = find_config(root)
        assert found == config_path


def test_find_config_in_parent() -> None:
    """Test finding config in parent directory."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config_path = root / CONFIG_FILENAME
        config_path.write_text('[spec]\nname = "test"\n')

        subdir = root / "subdir" / "nested"
        subdir.mkdir(parents=True)

        found = find_config(subdir)
        assert found == config_path


def test_find_config_not_found() -> None:
    """Test when config is not found."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        found = find_config(root)
        assert found is None


def test_find_config_default_cwd() -> None:
    """Test find_config uses cwd as default."""
    # This just verifies it doesn't crash
    result = find_config()
    # May or may not find a config depending on where tests run
    assert result is None or result.name == CONFIG_FILENAME


def test_get_project_root() -> None:
    """Test getting project root from config path."""
    config_path = Path("/some/project/certo.toml")
    assert get_project_root(config_path) == Path("/some/project")


def test_get_cache_dir() -> None:
    """Test getting cache directory."""
    project_root = Path("/some/project")
    assert get_cache_dir(project_root) == Path("/some/project") / CACHE_DIRNAME


def test_ensure_cache_dir_creates() -> None:
    """Test ensure_cache_dir creates directory."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        cache_dir = ensure_cache_dir(root)

        assert cache_dir.is_dir()
        assert cache_dir == root / CACHE_DIRNAME
        assert (cache_dir / ".gitignore").exists()


def test_ensure_cache_dir_gitignore_contents() -> None:
    """Test ensure_cache_dir creates proper .gitignore."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        cache_dir = ensure_cache_dir(root)

        gitignore = cache_dir / ".gitignore"
        assert gitignore.read_text() == "*\n"


def test_ensure_cache_dir_idempotent() -> None:
    """Test ensure_cache_dir is idempotent."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Call twice
        cache_dir1 = ensure_cache_dir(root)
        cache_dir2 = ensure_cache_dir(root)

        assert cache_dir1 == cache_dir2
        assert cache_dir1.is_dir()


def test_ensure_cache_dir_preserves_existing_gitignore() -> None:
    """Test ensure_cache_dir doesn't overwrite existing .gitignore."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        cache_dir = root / CACHE_DIRNAME
        cache_dir.mkdir()

        # Create custom .gitignore
        gitignore = cache_dir / ".gitignore"
        gitignore.write_text("# Custom\n*.log\n")

        # Call ensure_cache_dir
        ensure_cache_dir(root)

        # Should preserve existing content
        assert gitignore.read_text() == "# Custom\n*.log\n"


def test_get_config_path_stdin() -> None:
    """Test get_config_path with stdin (-) config."""
    from argparse import Namespace
    from certo.cli.output import Output, OutputFormat, get_config_path

    args = Namespace(config="-", path=None)
    output = Output(quiet=False, verbose=False, fmt=OutputFormat.TEXT)

    result = get_config_path(args, output)
    assert result is None


def test_get_config_path_explicit() -> None:
    """Test get_config_path with explicit config path."""
    from argparse import Namespace
    from certo.cli.output import Output, OutputFormat, get_config_path

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config_path = root / "custom.toml"
        config_path.write_text('[spec]\nname = "test"\n')

        args = Namespace(config=str(config_path), path=None)
        output = Output(quiet=False, verbose=False, fmt=OutputFormat.TEXT)

        result = get_config_path(args, output)
        assert result == config_path


def test_get_config_path_explicit_not_found() -> None:
    """Test get_config_path with non-existent explicit config."""
    from argparse import Namespace
    from certo.cli.output import Output, OutputFormat, get_config_path

    args = Namespace(config="/nonexistent/path.toml", path=None)
    output = Output(quiet=False, verbose=False, fmt=OutputFormat.TEXT)

    result = get_config_path(args, output)
    assert result is None


def test_get_config_path_via_path_arg() -> None:
    """Test get_config_path with --path argument."""
    from argparse import Namespace
    from certo.cli.output import Output, OutputFormat, get_config_path

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config_path = root / "certo.toml"
        config_path.write_text('[spec]\nname = "test"\n')

        args = Namespace(config=None, path=root)
        output = Output(quiet=False, verbose=False, fmt=OutputFormat.TEXT)

        result = get_config_path(args, output)
        assert result == config_path
