"""Init command implementation."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from certo.cli.output import Output
from certo.spec import Spec, now_utc


def cmd_init(args: Namespace, output: Output) -> int:
    """Initialize a new certo spec."""
    root: Path = args.path
    certo_dir = root / ".certo"
    spec_path = certo_dir / "spec.toml"

    # Check if spec already exists
    if spec_path.exists() and not getattr(args, "force", False):
        output.error(f"Spec already exists at {spec_path}")
        output.error("Use --force to overwrite")
        return 1

    # Determine project name
    name = getattr(args, "name", None) or root.resolve().name

    # Create directory structure
    certo_dir.mkdir(exist_ok=True)

    # Create cache directory with .gitignore
    cache_dir = certo_dir / "cache"
    cache_dir.mkdir(exist_ok=True)
    (cache_dir / ".gitignore").write_text("# Ignore all cache contents\n*\n")

    # Create spec
    spec = Spec(
        name=name,
        version=1,
        created=now_utc(),
    )
    spec.save(spec_path)

    output.success(f"Initialized certo spec at {spec_path}")
    output.json_output(
        {
            "path": str(spec_path),
            "name": name,
        }
    )

    return 0
