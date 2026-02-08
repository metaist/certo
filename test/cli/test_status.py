"""Tests for certo.cli.status module - non-example tests."""

from __future__ import annotations

from certo.cli.status import _get_item_type


def test_get_item_type() -> None:
    """Test _get_item_type function."""
    assert _get_item_type("c-abc1234") == "claim"
    assert _get_item_type("c-xyz") == "claim"
    assert _get_item_type("k-abc1234") == "check"
    assert _get_item_type("k-xyz") == "check"
    assert _get_item_type("i-abc1234") is None  # issues dropped
    assert _get_item_type("d1") is None
    assert _get_item_type("unknown") is None


def test_status_claim_detail_all_fields() -> None:
    """Test status shows all claim detail fields."""
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from certo.cli import main

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "certo.toml").write_text("""
[certo]
name = "test"
version = 1

[[claims]]
id = "c-test123"
text = "Test claim"
status = "confirmed"
author = "tester"
tags = ["tag1", "tag2"]
why = "Because reasons"
considered = ["Alternative 1", "Alternative 2"]
evidence = ["evidence1.json"]
traces_to = ["req-001"]
supersedes = "c-old"
closes = ["i-issue"]
created = 2026-02-05T12:00:00Z
updated = 2026-02-06T12:00:00Z

[claims.verify]
"k-test.passed" = { eq = true }
""")
        result = main(["status", "c-test123", "--path", tmpdir])
        assert result == 0
