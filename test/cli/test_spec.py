"""Tests for certo.cli.spec module."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from certo.cli import main
from certo.cli.spec import _get_item_type

if TYPE_CHECKING:
    from pytest import CaptureFixture


def test_main_spec_no_subcommand(capsys: CaptureFixture[str]) -> None:
    """Test plan command without subcommand shows help."""
    result = main(["spec"])
    assert result == 0
    captured = capsys.readouterr()
    assert "show" in captured.out


def test_main_spec_show(capsys: CaptureFixture[str]) -> None:
    """Test plan show command."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"
status = "confirmed"

[[concerns]]
id = "c1"
claim = "Test claim"
category = "functional"
""")

        result = main(["spec", "show", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Decisions:" in captured.out
        assert "d1" in captured.out
        assert "Test decision" in captured.out
        assert "Concerns:" in captured.out
        assert "c1" in captured.out
        assert "Test claim" in captured.out


def test_main_spec_show_missing_blueprint(capsys: CaptureFixture[str]) -> None:
    """Test plan show with missing blueprint."""
    with TemporaryDirectory() as tmpdir:
        result = main(["spec", "show", tmpdir])
        assert result == 1
        captured = capsys.readouterr()
        assert "no spec" in captured.err.lower()


def test_main_spec_show_decisions_only(capsys: CaptureFixture[str]) -> None:
    """Test plan show --decisions."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"

[[concerns]]
id = "c1"
claim = "Test claim"
""")

        result = main(["spec", "show", "--decisions", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Decisions:" in captured.out
        assert "d1" in captured.out
        assert "Concerns:" not in captured.out


def test_main_spec_show_concerns_only(capsys: CaptureFixture[str]) -> None:
    """Test plan show --concerns."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"

[[concerns]]
id = "c1"
claim = "Test claim"
""")

        result = main(["spec", "show", "--concerns", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Concerns:" in captured.out
        assert "c1" in captured.out
        assert "Decisions:" not in captured.out


def test_main_spec_show_verbose(capsys: CaptureFixture[str]) -> None:
    """Test plan show -v."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"
description = "A longer description of the decision"
decided_by = "metaist"
decided_on = 2026-02-05T12:00:00Z

[[concerns]]
id = "c1"
claim = "Test claim"
strategy = "llm"
failure = "warn"
traces_to = ["d1"]
""")

        result = main(["-v", "spec", "show", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "A longer description" in captured.out
        assert "metaist" in captured.out
        assert "Strategy:" in captured.out
        assert "Traces to:" in captured.out


def test_main_spec_show_decision_detail(capsys: CaptureFixture[str]) -> None:
    """Test plan show <decision_id>."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"
status = "confirmed"
description = "Full description here"
alternatives = ["alt1", "alt2"]
rationale = "Because reasons"
decided_by = "metaist"
decided_on = 2026-02-05T12:00:00Z
""")

        result = main(["spec", "show", tmpdir, "d1"])
        assert result == 0
        captured = capsys.readouterr()
        assert "d1: Test decision" in captured.out
        assert "Status: confirmed" in captured.out
        assert "Full description here" in captured.out
        assert "alt1" in captured.out
        assert "alt2" in captured.out
        assert "Because reasons" in captured.out
        assert "metaist" in captured.out


def test_main_spec_show_concern_detail(capsys: CaptureFixture[str]) -> None:
    """Test plan show <concern_id>."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[concerns]]
id = "c1"
claim = "Test claim"
category = "functional"
strategy = "llm"
context = ["README.md"]
verify_with = ["test"]
conditions = ["condition1"]
failure = "block-commit"
traces_to = ["d1"]
""")

        result = main(["spec", "show", tmpdir, "c1"])
        assert result == 0
        captured = capsys.readouterr()
        assert "c1: Test claim" in captured.out
        assert "Category: functional" in captured.out
        assert "Strategy: llm" in captured.out
        assert "Failure: block-commit" in captured.out
        assert "condition1" in captured.out
        assert "README.md" in captured.out
        assert "Verify with: test" in captured.out
        assert "Traces to: d1" in captured.out


def test_main_spec_show_missing_decision(capsys: CaptureFixture[str]) -> None:
    """Test plan show with missing decision ID."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text('[spec]\nname = "test"\n')

        result = main(["spec", "show", tmpdir, "d999"])
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()


def test_main_spec_show_missing_concern(capsys: CaptureFixture[str]) -> None:
    """Test plan show with missing concern ID."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text('[spec]\nname = "test"\n')

        result = main(["spec", "show", tmpdir, "c999"])
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()


def test_main_spec_show_unknown_id(capsys: CaptureFixture[str]) -> None:
    """Test plan show with unknown ID prefix."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text('[spec]\nname = "test"\n')

        result = main(["spec", "show", tmpdir, "x1"])
        assert result == 1
        captured = capsys.readouterr()
        assert "unknown" in captured.err.lower()


def test_main_spec_show_json(capsys: CaptureFixture[str]) -> None:
    """Test plan show with JSON output."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"

[[concerns]]
id = "c1"
claim = "Test claim"
""")

        result = main(["--format", "json", "spec", "show", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "decisions" in data
        assert "concerns" in data
        assert len(data["decisions"]) == 1
        assert len(data["concerns"]) == 1


def test_main_spec_show_decision_json(capsys: CaptureFixture[str]) -> None:
    """Test plan show <decision_id> with JSON output."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"
status = "confirmed"
""")

        result = main(["--format", "json", "spec", "show", tmpdir, "d1"])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["id"] == "d1"
        assert data["title"] == "Test decision"
        assert data["status"] == "confirmed"


def test_main_spec_show_contexts(capsys: CaptureFixture[str]) -> None:
    """Test plan show --contexts."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[contexts]]
id = "ctx1"
name = "Test context"
description = "A test context"
expires = 2026-12-31T00:00:00Z
""")

        result = main(["spec", "show", "--contexts", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Contexts:" in captured.out
        assert "ctx1" in captured.out
        assert "Test context" in captured.out


def test_main_spec_show_context_detail(capsys: CaptureFixture[str]) -> None:
    """Test plan show <context_id>."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[contexts]]
id = "ctx1"
name = "Test context"
description = "Full context description"
applies_to = ["c1", "c2"]
expires = 2026-12-31T00:00:00Z

[contexts.overrides]
strategy = "static"
""")

        result = main(["spec", "show", tmpdir, "ctx1"])
        assert result == 0
        captured = capsys.readouterr()
        assert "ctx1: Test context" in captured.out
        assert "Full context description" in captured.out
        assert "c1" in captured.out
        assert "c2" in captured.out
        assert "2026-12-31" in captured.out
        assert "strategy" in captured.out


def test_main_spec_show_missing_context(capsys: CaptureFixture[str]) -> None:
    """Test plan show with missing context ID."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text('[spec]\nname = "test"\n')

        result = main(["spec", "show", tmpdir, "ctx999"])
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()


def test_main_spec_show_contexts_verbose(capsys: CaptureFixture[str]) -> None:
    """Test plan show --contexts -v."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[contexts]]
id = "ctx1"
name = "Test context"
description = "A test context description"
expires = 2026-12-31T00:00:00Z
""")

        result = main(["-v", "spec", "show", "--contexts", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "A test context" in captured.out
        assert "Expires:" in captured.out


def test_main_spec_show_decision_superseded(capsys: CaptureFixture[str]) -> None:
    """Test plan show with superseded decision."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Old decision"
status = "superseded"

[[decisions]]
id = "d2"
title = "Deferred decision"
status = "deferred"

[[decisions]]
id = "d3"
title = "Proposed decision"
status = "proposed"
""")

        result = main(["spec", "show", "--decisions", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "[superseded]" in captured.out
        assert "[deferred]" in captured.out
        assert "[proposed]" in captured.out


def test_get_item_type() -> None:
    """Test _get_item_type function."""
    assert _get_item_type("d1") == "decision"
    assert _get_item_type("d123") == "decision"
    assert _get_item_type("c1") == "concern"
    assert _get_item_type("c99") == "concern"
    assert _get_item_type("ctx1") == "context"
    assert _get_item_type("ctx123") == "context"
    assert _get_item_type("x1") is None
    assert _get_item_type("unknown") is None


def test_main_spec_show_all_with_newlines(capsys: CaptureFixture[str]) -> None:
    """Test plan show with all sections shows newlines between."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"

[[concerns]]
id = "c1"
claim = "Test claim"

[[contexts]]
id = "ctx1"
name = "Test context"
""")

        result = main(["spec", "show", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "Decisions:" in captured.out
        assert "Concerns:" in captured.out
        assert "Contexts:" in captured.out


def test_main_spec_show_verbose_long_description(capsys: CaptureFixture[str]) -> None:
    """Test plan show -v truncates long descriptions."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        long_desc = "A" * 100  # More than 60 chars
        blueprint.write_text(f'''
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"
description = "{long_desc}"
decided_by = "tester"
''')

        result = main(["-v", "spec", "show", "--decisions", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "..." in captured.out  # truncated


def test_main_spec_show_decision_without_date(capsys: CaptureFixture[str]) -> None:
    """Test plan show -v with decision that has no date."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"
description = "A decision"
decided_by = "tester"
""")

        result = main(["-v", "spec", "show", "--decisions", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "tester" in captured.out


def test_main_spec_show_context_verbose_long_desc(capsys: CaptureFixture[str]) -> None:
    """Test plan show -v contexts with long descriptions."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        long_desc = "B" * 100
        blueprint.write_text(f'''
[spec]
name = "test"

[[contexts]]
id = "ctx1"
name = "Test context"
description = "{long_desc}"
''')

        result = main(["-v", "spec", "show", "--contexts", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "..." in captured.out


def test_main_spec_show_concern_no_category(capsys: CaptureFixture[str]) -> None:
    """Test plan show concern detail without category."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[concerns]]
id = "c1"
claim = "Test claim"
""")

        result = main(["spec", "show", tmpdir, "c1"])
        assert result == 0
        captured = capsys.readouterr()
        assert "c1: Test claim" in captured.out
        assert "Category:" not in captured.out  # No category field shown


def test_main_spec_show_verbose_no_description(capsys: CaptureFixture[str]) -> None:
    """Test plan show -v with decision that has no description."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"
decided_by = "tester"
decided_on = 2026-02-05T12:00:00Z
""")

        result = main(["-v", "spec", "show", "--decisions", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "d1" in captured.out
        assert "tester" in captured.out


def test_main_spec_show_verbose_context_no_description(
    capsys: CaptureFixture[str],
) -> None:
    """Test plan show -v with context that has no description."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[contexts]]
id = "ctx1"
name = "Test context"
expires = 2026-12-31T00:00:00Z
""")

        result = main(["-v", "spec", "show", "--contexts", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "ctx1" in captured.out
        assert "Expires:" in captured.out


def test_main_spec_show_verbose_context_no_expires(capsys: CaptureFixture[str]) -> None:
    """Test plan show -v with context that has no expiration."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[contexts]]
id = "ctx1"
name = "Test context"
description = "A description"
""")

        result = main(["-v", "spec", "show", "--contexts", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "ctx1" in captured.out
        assert "A description" in captured.out
        assert "Expires:" not in captured.out


def test_main_spec_show_verbose_decision_no_decided_by(
    capsys: CaptureFixture[str],
) -> None:
    """Test plan show -v with decision that has no decided_by."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[decisions]]
id = "d1"
title = "Test decision"
description = "A description"
""")

        result = main(["-v", "spec", "show", "--decisions", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "d1" in captured.out
        assert "A description" in captured.out
        assert "Decided by" not in captured.out


def test_main_spec_show_context_detail_minimal(capsys: CaptureFixture[str]) -> None:
    """Test plan show context detail with minimal fields."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[contexts]]
id = "ctx1"
name = "Minimal context"
""")

        result = main(["spec", "show", tmpdir, "ctx1"])
        assert result == 0
        captured = capsys.readouterr()
        assert "ctx1: Minimal context" in captured.out
        assert "Applies to:" not in captured.out
        assert "Expires:" not in captured.out
        assert "Overrides:" not in captured.out


def test_main_spec_show_verbose_concern_no_traces(capsys: CaptureFixture[str]) -> None:
    """Test plan show -v with concern that has no traces_to."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        certo_dir = root / ".certo"
        certo_dir.mkdir()
        blueprint = certo_dir / "spec.toml"
        blueprint.write_text("""
[spec]
name = "test"

[[concerns]]
id = "c1"
claim = "Test claim"
strategy = "static"
""")

        result = main(["-v", "spec", "show", "--concerns", tmpdir])
        assert result == 0
        captured = capsys.readouterr()
        assert "c1" in captured.out
        assert "Strategy: static" in captured.out
        assert "Traces to:" not in captured.out
