"""CLI output utilities."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from enum import Enum
from pathlib import Path
from typing import Any


class OutputFormat(Enum):
    """Output format options."""

    TEXT = "text"
    JSON = "json"


class Output:
    """Handle output based on verbosity and format settings."""

    def __init__(
        self, *, quiet: bool = False, verbose: bool = False, fmt: OutputFormat
    ) -> None:
        self.quiet = quiet
        self.verbose = verbose
        self.format = fmt
        self._json_data: dict[str, Any] = {}

    def info(self, message: str) -> None:
        """Print info message (normal and verbose mode only)."""
        if not self.quiet and self.format == OutputFormat.TEXT:
            print(message)

    def success(self, message: str) -> None:
        """Print success message (normal and verbose mode only)."""
        if not self.quiet and self.format == OutputFormat.TEXT:
            print(message)

    def verbose_info(self, message: str) -> None:
        """Print verbose message (verbose mode only)."""
        if self.verbose and self.format == OutputFormat.TEXT:
            print(message)

    def error(self, message: str) -> None:
        """Print error message (always in text mode, collected for JSON)."""
        if self.format == OutputFormat.TEXT:
            print(message, file=sys.stderr)

    def json_output(self, data: dict[str, Any]) -> None:
        """Set JSON output data."""
        self._json_data = data

    def finalize(self) -> None:
        """Finalize output (print JSON if in JSON mode)."""
        if self.format == OutputFormat.JSON:
            print(json.dumps(self._json_data, default=str))


def get_config_path(args: Namespace, output: Output) -> Path | None:
    """Get config path from args, with error handling.

    Priority:
    1. --config (explicit path or '-' for stdin)
    2. --path/certo.toml (deprecated)
    3. find_config() from cwd

    Returns:
        Path to config file, or None if not found (after printing error)
    """
    from certo.config import CONFIG_FILENAME, find_config

    # Explicit --config
    config_arg = getattr(args, "config", None)
    if config_arg == "-":
        output.error("stdin config not yet implemented")
        return None
    if config_arg:
        config_path = Path(config_arg)
        if not config_path.exists():
            output.error(f"Config not found: {config_path}")
            return None
        return config_path

    # Deprecated --path (look for certo.toml in that directory)
    path_arg: Path | None = getattr(args, "path", None)
    if path_arg:
        config_in_path = path_arg / CONFIG_FILENAME
        if config_in_path.exists():
            return config_in_path
        # Fall through to find_config from path

    # Find config by walking up
    start: Path = path_arg if path_arg else Path.cwd()
    found_config = find_config(start)
    if found_config is None:
        output.error(f"No {CONFIG_FILENAME} found (searched from {start})")
        return None
    return found_config
