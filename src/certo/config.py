"""Configuration utilities for certo."""

from __future__ import annotations

from pathlib import Path

CONFIG_FILENAME = "certo.toml"
CACHE_DIRNAME = ".certo_cache"


def find_config(start: Path | None = None) -> Path | None:
    """Find certo.toml by walking up from start directory.

    Like git finding .git, walks up parent directories until finding
    certo.toml or reaching filesystem root.

    Args:
        start: Directory to start searching from (default: cwd)

    Returns:
        Path to certo.toml if found, None otherwise
    """
    if start is None:
        start = Path.cwd()

    current = start.resolve()
    while True:
        config_path = current / CONFIG_FILENAME
        if config_path.exists():
            return config_path

        parent = current.parent
        if parent == current:
            # Reached filesystem root
            return None
        current = parent


def get_project_root(config_path: Path) -> Path:
    """Get project root from config path.

    Args:
        config_path: Path to certo.toml

    Returns:
        Parent directory of certo.toml (the project root)
    """
    return config_path.parent


def get_cache_dir(project_root: Path) -> Path:
    """Get cache directory for a project.

    Args:
        project_root: Project root directory

    Returns:
        Path to .certo_cache directory
    """
    return project_root / CACHE_DIRNAME


def ensure_cache_dir(project_root: Path) -> Path:
    """Ensure cache directory exists with proper .gitignore.

    Creates .certo_cache/ if it doesn't exist, and adds a .gitignore
    with '*' if one doesn't exist (allowing users to override if they
    want to commit cache contents).

    Args:
        project_root: Project root directory

    Returns:
        Path to .certo_cache directory
    """
    cache_dir = get_cache_dir(project_root)
    cache_dir.mkdir(parents=True, exist_ok=True)

    gitignore = cache_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n")

    return cache_dir
