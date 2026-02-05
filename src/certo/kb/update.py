"""Update knowledge base from authoritative sources."""

from __future__ import annotations

import tomllib
import urllib.request
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path


def get_kb_path() -> Path:
    """Get the path to the knowledge base directory."""
    kb_files = resources.files("certo.kb")
    # Convert to actual path for writing
    # This only works when installed in editable mode or from source
    return Path(str(kb_files))


def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    with urllib.request.urlopen(url) as response:  # noqa: S310
        content: str = response.read().decode("utf-8")
        return content


def get_latest_commit(repo_url: str) -> str:
    """Get the latest commit SHA for a GitHub repo."""
    # Extract owner/repo from URL
    # https://github.com/python/typeshed -> python/typeshed
    parts = repo_url.rstrip("/").split("/")
    owner, repo = parts[-2], parts[-1]

    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/main"
    content = fetch_url(api_url)

    # Simple JSON parsing for commit SHA
    import json

    data = json.loads(content)
    sha: str = data["sha"]
    return sha


def update_source(source_path: Path, verbose: bool = False) -> bool:
    """Update a single knowledge source.

    Args:
        source_path: Path to the source directory containing meta.toml
        verbose: Whether to print verbose output

    Returns:
        True if updated successfully, False otherwise
    """
    meta_path = source_path / "meta.toml"
    if not meta_path.exists():
        return False

    with meta_path.open("rb") as f:
        meta = tomllib.load(f)

    source = meta["source"]
    repo_url = source["url"]
    files = source["files"]

    if verbose:
        print(f"Updating {source['name']} from {repo_url}")

    # Get latest commit
    latest_commit = get_latest_commit(repo_url)
    if verbose:
        print(f"  Latest commit: {latest_commit}")

    # Fetch files
    for file_path in files:
        raw_url = f"https://raw.githubusercontent.com/{repo_url.split('github.com/')[-1]}/main/{file_path}"
        if verbose:
            print(f"  Fetching {file_path}")

        content = fetch_url(raw_url)

        # Determine local filename
        local_name = Path(file_path).name
        local_path = source_path / local_name

        local_path.write_text(content)

    # Update meta.toml
    new_meta = f"""[source]
name = "{source["name"]}"
url = "{repo_url}"
commit = "{latest_commit}"
updated_at = {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
license = "{source["license"]}"
files = {files!r}
"""
    # Fix the list formatting
    new_meta = (
        new_meta.replace("['", '[\n  "')
        .replace("', '", '",\n  "')
        .replace("']", '",\n]')
    )

    meta_path.write_text(new_meta)

    if verbose:
        print(f"  Updated to commit {latest_commit[:12]}")

    return True


def update_all(verbose: bool = False) -> int:
    """Update all knowledge sources.

    Returns:
        Number of sources updated
    """
    kb_path = get_kb_path()
    updated = 0

    # Find all meta.toml files
    for meta_file in kb_path.rglob("meta.toml"):
        source_path = meta_file.parent
        if update_source(source_path, verbose=verbose):
            updated += 1

    return updated


def update_python(verbose: bool = False) -> bool:
    """Update Python knowledge sources.

    Returns:
        True if updated successfully
    """
    kb_path = get_kb_path()
    python_path = kb_path / "python" / "typeshed"

    if not python_path.exists():
        return False

    return update_source(python_path, verbose=verbose)
