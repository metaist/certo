"""Init command implementation."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from certo.cli.output import Output
from certo.config import CONFIG_FILENAME, ensure_cache_dir
from certo.spec import Spec


def cmd_init(args: Namespace, output: Output) -> int:
    """Initialize a new certo spec."""
    root: Path = args.path
    config_path = root / CONFIG_FILENAME

    # Check if spec already exists
    if config_path.exists() and not getattr(args, "force", False):
        output.error(f"Spec already exists at {config_path}")
        output.error("Use --force to overwrite")
        return 1

    # Ensure cache directory exists
    ensure_cache_dir(root)

    # Create spec
    spec = Spec(version=1)
    spec.save(config_path)

    output.success(f"Initialized certo spec at {config_path}")
    output.json_output({"path": str(config_path)})

    return 0
