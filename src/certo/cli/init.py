"""Init command implementation."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from certo.cli.output import Output
from certo.config import CONFIG_FILENAME, ensure_cache_dir
from certo.spec import Spec, now_utc


def cmd_init(args: Namespace, output: Output) -> int:
    """Initialize a new certo spec."""
    root: Path = args.path
    config_path = root / CONFIG_FILENAME

    # Check if spec already exists
    if config_path.exists() and not getattr(args, "force", False):
        output.error(f"Spec already exists at {config_path}")
        output.error("Use --force to overwrite")
        return 1

    # Determine project name
    name = getattr(args, "name", None) or root.resolve().name

    # Ensure cache directory exists
    ensure_cache_dir(root)

    # Create spec
    spec = Spec(
        name=name,
        version=1,
        created=now_utc(),
    )
    spec.save(config_path)

    output.success(f"Initialized certo spec at {config_path}")
    output.json_output(
        {
            "path": str(config_path),
            "name": name,
        }
    )

    return 0
