"""Tests for certo."""

from __future__ import annotations

import certo


def test_version() -> None:
    """Check version is set."""
    assert certo.__version__
