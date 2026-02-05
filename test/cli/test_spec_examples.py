"""Example-driven tests for certo spec show command.

This module parses markdown files in test/cli/examples/ and runs them as tests.
Each markdown file contains multiple test scenarios with:
- Optional TOML spec content
- Bash command to run
- Expected/Not Expected output patterns
- Optional exit code
- Optional expected stderr
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest

from certo.cli import main

if TYPE_CHECKING:
    from pytest import CaptureFixture

EXAMPLES_DIR = Path(__file__).parent / "examples"


@dataclass
class ExampleCase:
    """A single test case parsed from markdown."""

    name: str
    spec_content: str | None = None
    command: list[str] = field(default_factory=list)
    expected: list[str] = field(default_factory=list)
    not_expected: list[str] = field(default_factory=list)
    expected_stderr: list[str] = field(default_factory=list)
    exit_code: int = 0
    source_file: str = ""
    line_number: int = 0


def parse_markdown_examples(path: Path) -> list[ExampleCase]:
    """Parse a markdown file into test cases."""
    content = path.read_text()
    cases: list[ExampleCase] = []

    # Split by ## headers (test case boundaries)
    sections = re.split(r"^## ", content, flags=re.MULTILINE)

    for section in sections[1:]:  # Skip content before first ##
        lines = section.split("\n")
        name = lines[0].strip()

        case = ExampleCase(name=name, source_file=path.name)

        # Find line number for better error reporting
        case.line_number = content.find(f"## {name}") + 1

        # Parse the section
        i = 1
        while i < len(lines):
            line = lines[i]

            # TOML code block
            if line.startswith("```toml"):
                i += 1
                toml_lines = []
                while i < len(lines) and not lines[i].startswith("```"):
                    toml_lines.append(lines[i])
                    i += 1
                case.spec_content = "\n".join(toml_lines)
                i += 1
                continue

            # Bash command
            if line.startswith("```bash"):
                i += 1
                if i < len(lines):
                    cmd = lines[i].strip()
                    # Parse command into args, replacing 'certo' with nothing
                    # since we call main() directly
                    args = cmd.split()
                    if args and args[0] == "certo":
                        args = args[1:]
                    case.command = args
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    i += 1
                i += 1
                continue

            # Expected output
            if line.startswith("**Expected**"):
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    i += 1
                if i < len(lines):
                    i += 1  # skip ```
                    expected_lines = []
                    while i < len(lines) and not lines[i].startswith("```"):
                        expected_lines.append(lines[i])
                        i += 1
                    case.expected = [line for line in expected_lines if line.strip()]
                    i += 1
                continue

            # Not expected output
            if line.startswith("**Not Expected**"):
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    i += 1
                if i < len(lines):
                    i += 1  # skip ```
                    not_expected_lines = []
                    while i < len(lines) and not lines[i].startswith("```"):
                        not_expected_lines.append(lines[i])
                        i += 1
                    case.not_expected = [
                        line for line in not_expected_lines if line.strip()
                    ]
                    i += 1
                continue

            # Expected stderr
            if line.startswith("**Expected Stderr**"):
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    i += 1
                if i < len(lines):
                    i += 1  # skip ```
                    stderr_lines = []
                    while i < len(lines) and not lines[i].startswith("```"):
                        stderr_lines.append(lines[i])
                        i += 1
                    case.expected_stderr = [
                        line for line in stderr_lines if line.strip()
                    ]
                    i += 1
                continue

            # Exit code
            if line.startswith("**Exit Code:**"):
                match = re.search(r"\*\*Exit Code:\*\*\s*(\d+)", line)
                if match:
                    case.exit_code = int(match.group(1))
                i += 1
                continue

            i += 1

        if case.command:  # Only add if we have a command
            cases.append(case)

    return cases


def collect_all_examples() -> list[ExampleCase]:
    """Collect all test cases from all example files."""
    cases = []
    for md_file in sorted(EXAMPLES_DIR.glob("*.md")):
        cases.extend(parse_markdown_examples(md_file))
    return cases


# Collect test cases at module load time
ALL_CASES = collect_all_examples()


def case_id(case: ExampleCase) -> str:
    """Generate a test ID for a case."""
    # Clean up name for pytest ID
    name = case.name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")
    return f"{case.source_file}::{name}"


@pytest.mark.parametrize("case", ALL_CASES, ids=case_id)
def test_spec_example(case: ExampleCase, capsys: CaptureFixture[str]) -> None:
    """Run a single example test case."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Set up spec file if provided
        if case.spec_content is not None:
            certo_dir = root / ".certo"
            certo_dir.mkdir()
            spec = certo_dir / "spec.toml"
            spec.write_text(case.spec_content)

        # Build command args, appending tmpdir as path for spec commands
        args = list(case.command)
        if "spec" in args and "show" in args:
            # Find position after 'show' to insert path
            # Handle: spec show, spec show --claims, spec show c-xxx
            show_idx = args.index("show")
            # Check if there's already a path-like argument or ID after show
            insert_idx = show_idx + 1
            while insert_idx < len(args) and args[insert_idx].startswith("-"):
                insert_idx += 1
            # If the next arg looks like an ID (starts with c-, i-, x-), insert before it
            if insert_idx < len(args) and re.match(r"^[cix]-", args[insert_idx]):
                args.insert(insert_idx, tmpdir)
            elif insert_idx >= len(args):
                args.append(tmpdir)
            else:
                # There's already something there that's not an ID
                args.insert(insert_idx, tmpdir)

        # Run command
        result = main(args)
        captured = capsys.readouterr()

        # Check exit code
        assert result == case.exit_code, (
            f"Expected exit code {case.exit_code}, got {result}\n"
            f"stdout: {captured.out}\n"
            f"stderr: {captured.err}"
        )

        # Check expected patterns in stdout
        for pattern in case.expected:
            assert pattern in captured.out, (
                f"Expected '{pattern}' in stdout\n"
                f"stdout: {captured.out}\n"
                f"File: {case.source_file}, test: {case.name}"
            )

        # Check not-expected patterns not in stdout
        for pattern in case.not_expected:
            assert pattern not in captured.out, (
                f"Did not expect '{pattern}' in stdout\n"
                f"stdout: {captured.out}\n"
                f"File: {case.source_file}, test: {case.name}"
            )

        # Check expected stderr patterns (case-insensitive)
        for pattern in case.expected_stderr:
            assert pattern.lower() in captured.err.lower(), (
                f"Expected '{pattern}' in stderr\n"
                f"stderr: {captured.err}\n"
                f"File: {case.source_file}, test: {case.name}"
            )
