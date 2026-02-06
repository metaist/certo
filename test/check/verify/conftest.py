"""Shared fixtures for verification tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from certo.check.core import Evidence
from certo.check.shell import ShellEvidence
from certo.check.url import UrlEvidence


@pytest.fixture
def evidence_map() -> dict[str, Evidence]:
    """Create a sample evidence map for testing."""
    now = datetime.now(timezone.utc)
    return {
        "k-pytest": ShellEvidence(
            check_id="k-pytest",
            kind="shell",
            timestamp=now,
            duration=7.2,
            exit_code=0,
            stdout="411 passed in 7.2s",
            stderr="",
            json={
                "totals": {"percent_covered": 100.0},
            },
        ),
        "k-ruff": ShellEvidence(
            check_id="k-ruff",
            kind="shell",
            timestamp=now,
            duration=0.3,
            exit_code=0,
            stdout="All checks passed!",
            stderr="",
        ),
        "k-failing": ShellEvidence(
            check_id="k-failing",
            kind="shell",
            timestamp=now,
            duration=1.0,
            exit_code=1,
            stdout="",
            stderr="Error: something went wrong",
        ),
        "k-python-eol": UrlEvidence(
            check_id="k-python-eol",
            kind="url",
            timestamp=now,
            duration=0.5,
            status_code=200,
            body="[]",
        ),
    }
