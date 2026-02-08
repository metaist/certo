"""Selector parsing and resolution for fact queries."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import Any

from certo.probe.core import Fact


@dataclass
class Selector:
    """A parsed selector for accessing fact data."""

    segments: list[str]  # Each segment is a literal or glob pattern

    def __str__(self) -> str:
        """Format selector back to string."""
        parts = []
        for seg in self.segments:
            # Use brackets if segment contains dots or special chars
            if "." in seg or "/" in seg:
                parts.append(f"[{seg}]")
            else:
                parts.append(seg)
        return ".".join(parts)


def parse_selector(selector: str) -> Selector:
    """Parse a selector string into segments.

    Supports:
    - Dot-separated segments: k-pytest.json.files
    - Bracket notation for special keys: k-pytest.json.files[src/certo/cli.py]
    - Wildcards: *.exit_code, k-pytest.json.files[*.py]

    Examples:
        "k-pytest.exit_code" -> ["k-pytest", "exit_code"]
        "k-pytest.json.files[src/certo/cli.py]" -> ["k-pytest", "json", "files", "src/certo/cli.py"]
        "*.exit_code" -> ["*", "exit_code"]
    """
    segments: list[str] = []
    i = 0
    current = ""

    while i < len(selector):
        char = selector[i]

        if char == ".":
            # End current segment
            if current:
                segments.append(current)
                current = ""
            i += 1

        elif char == "[":
            # End current segment if any
            if current:
                segments.append(current)
                current = ""

            # Find closing bracket
            j = i + 1
            while j < len(selector) and selector[j] != "]":
                j += 1

            if j >= len(selector):
                msg = f"Unclosed bracket in selector: {selector}"
                raise ValueError(msg)

            # Extract bracket content
            segments.append(selector[i + 1 : j])
            i = j + 1

            # Skip trailing dot if present
            if i < len(selector) and selector[i] == ".":
                i += 1

        else:
            current += char
            i += 1

    # Add final segment
    if current:
        segments.append(current)

    return Selector(segments=segments)


def _matches_pattern(value: str, pattern: str) -> bool:
    """Check if value matches a glob pattern."""
    return fnmatch.fnmatch(value, pattern)


def _has_glob(segment: str) -> bool:
    """Check if a segment contains glob wildcards."""
    return "*" in segment or "?" in segment


def resolve_selector(
    selector: Selector | str,
    fact_map: dict[str, Fact],
) -> list[tuple[str, Any]]:
    """Resolve a selector against facts, returning all matches.

    Returns list of (full_path, value) tuples.
    Globs expand to multiple matches.

    Args:
        selector: Parsed selector or selector string
        fact_map: Dict mapping probe_id to Fact

    Returns:
        List of (path, value) tuples for all matches
    """
    if isinstance(selector, str):
        selector = parse_selector(selector)

    if not selector.segments:
        return []

    # Start with fact map
    # First segment should match probe IDs
    first_seg = selector.segments[0]
    remaining = selector.segments[1:]

    results: list[tuple[str, Any]] = []

    if _has_glob(first_seg):
        # Match multiple probes
        for probe_id, fact in fact_map.items():
            if _matches_pattern(probe_id, first_seg):
                # Convert fact to dict for traversal
                data = fact.to_dict()
                sub_results = _resolve_path(remaining, data, probe_id)
                results.extend(sub_results)
    else:
        # Single probe
        if first_seg not in fact_map:
            return []
        data = fact_map[first_seg].to_dict()
        results = _resolve_path(remaining, data, first_seg)

    return results


def _resolve_path(
    segments: list[str],
    data: Any,
    prefix: str,
) -> list[tuple[str, Any]]:
    """Resolve remaining path segments against data.

    Returns list of (full_path, value) tuples.
    """
    if not segments:
        return [(prefix, data)]

    segment = segments[0]
    remaining = segments[1:]
    results: list[tuple[str, Any]] = []

    if _has_glob(segment):
        # Expand glob against current level
        match data:
            case dict():
                for key in data:
                    if _matches_pattern(str(key), segment):
                        new_prefix = f"{prefix}.{key}" if prefix else key
                        sub_results = _resolve_path(remaining, data[key], new_prefix)
                        results.extend(sub_results)
            case list():
                for i, item in enumerate(data):
                    if _matches_pattern(str(i), segment):
                        new_prefix = f"{prefix}[{i}]"
                        sub_results = _resolve_path(remaining, item, new_prefix)
                        results.extend(sub_results)
            case _:
                pass  # Scalar values don't support glob expansion
    else:
        # Direct access
        match data:
            case dict() if segment in data:
                new_prefix = f"{prefix}.{segment}" if prefix else segment
                sub_results = _resolve_path(remaining, data[segment], new_prefix)
                results.extend(sub_results)
            case list():
                try:
                    idx = int(segment)
                    if 0 <= idx < len(data):
                        new_prefix = f"{prefix}[{idx}]"
                        sub_results = _resolve_path(remaining, data[idx], new_prefix)
                        results.extend(sub_results)
                except ValueError:
                    pass  # Not a valid index
            case _:
                pass  # Segment not found or wrong data type

    return results


# Backward compat alias
Evidence = Fact
