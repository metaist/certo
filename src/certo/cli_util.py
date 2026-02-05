"""CLI utilities shared across commands."""

from __future__ import annotations

import json
import sys
from enum import Enum
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
