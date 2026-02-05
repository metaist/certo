"""LLM-based verification for concerns."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from certo.llm.provider import LLMResponse, call_llm

# Maximum file size for context (50KB)
MAX_CONTEXT_FILE_SIZE = 50 * 1024

VERIFY_SYSTEM_PROMPT = """\
You are a code verification assistant. Your job is to verify whether code \
satisfies a specific claim.

You will be given:
1. A claim that must be verified
2. The contents of relevant source files

Analyze the code carefully and determine if it satisfies the claim.

You MUST respond with ONLY a JSON object, no other text:
{"pass": true, "explanation": "reason"}
or
{"pass": false, "explanation": "reason"}

Be strict but fair. If the claim is clearly satisfied, pass. If there are \
gaps or issues, fail with a specific explanation of what is missing or wrong.
"""


class VerificationError(Exception):
    """Error during verification."""


class FileTooLargeError(VerificationError):
    """A context file exceeds the size limit."""


class FileMissingError(VerificationError):
    """A context file does not exist."""


@dataclass
class VerificationResult:
    """Result of an LLM verification."""

    passed: bool
    explanation: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float = 0.0
    cached: bool = False
    cache_key: str = ""
    timestamp: datetime | None = None


def _hash_inputs(claim: str, context_contents: dict[str, str]) -> str:
    """Create a hash of the verification inputs for caching."""
    hasher = hashlib.sha256()
    hasher.update(claim.encode("utf-8"))
    for path in sorted(context_contents.keys()):
        hasher.update(path.encode("utf-8"))
        hasher.update(context_contents[path].encode("utf-8"))
    return hasher.hexdigest()[:16]


def _resolve_globs(patterns: list[str], project_root: Path) -> list[Path]:
    """Resolve glob patterns to file paths."""
    files: list[Path] = []
    for pattern in patterns:
        # Check if it's a literal file path first
        literal = project_root / pattern
        if literal.is_file():
            files.append(literal)
        else:
            # Treat as glob
            matches = list(project_root.glob(pattern))
            files.extend(p for p in matches if p.is_file())
    return sorted(set(files))


def _load_context(
    patterns: list[str], project_root: Path
) -> tuple[dict[str, str], list[Path]]:
    """Load context files, checking size limits.

    Returns:
        Tuple of (contents dict, list of resolved paths).

    Raises:
        FileMissingError: If no files match the patterns.
        FileTooLargeError: If any file exceeds the size limit.
    """
    files = _resolve_globs(patterns, project_root)

    if not files:
        raise FileMissingError(f"No files found matching context patterns: {patterns}")

    contents: dict[str, str] = {}
    for path in files:
        if not path.exists():
            raise FileMissingError(f"Context file not found: {path}")

        size = path.stat().st_size
        if size > MAX_CONTEXT_FILE_SIZE:
            raise FileTooLargeError(
                f"File {path} is {size:,} bytes, exceeds limit of "
                f"{MAX_CONTEXT_FILE_SIZE:,} bytes"
            )

        rel_path = str(path.relative_to(project_root))
        contents[rel_path] = path.read_text()

    return contents, files


def _build_prompt(claim: str, context_contents: dict[str, str]) -> str:
    """Build the verification prompt."""
    parts = [f"## Claim to verify\n\n{claim}\n"]

    parts.append("## Source files\n")
    for path, content in sorted(context_contents.items()):
        parts.append(f"### {path}\n\n```\n{content}\n```\n")

    return "\n".join(parts)


def _get_cache_path(project_root: Path, cache_key: str, concern_id: str) -> Path:
    """Get the path for a cached result."""
    cache_dir = project_root / ".certo" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{concern_id}-{cache_key}.toml"


def _load_cached_result(cache_path: Path) -> VerificationResult | None:
    """Load a cached verification result if it exists."""
    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "rb") as f:
            data = tomllib.load(f)

        return VerificationResult(
            passed=data["result"]["passed"],
            explanation=data["result"]["explanation"],
            model=data["meta"]["model"],
            prompt_tokens=data["meta"].get("prompt_tokens", 0),
            completion_tokens=data["meta"].get("completion_tokens", 0),
            total_tokens=data["meta"].get("total_tokens", 0),
            cost=data["meta"].get("cost", 0.0),
            cached=True,
            cache_key=data["meta"]["cache_key"],
            timestamp=datetime.fromisoformat(data["meta"]["timestamp"]),
        )
    except Exception:
        # Invalid cache, ignore
        return None


def _save_cached_result(
    cache_path: Path,
    result: VerificationResult,
    concern_id: str,
    claim: str,
    context_files: list[str],
) -> None:
    """Save a verification result to cache."""
    content = f'''# Verification cache for {concern_id}
# Generated by certo - do not edit manually

[meta]
concern_id = "{concern_id}"
cache_key = "{result.cache_key}"
timestamp = "{result.timestamp.isoformat() if result.timestamp else ""}"
model = "{result.model}"
prompt_tokens = {result.prompt_tokens}
completion_tokens = {result.completion_tokens}
total_tokens = {result.total_tokens}
cost = {result.cost}

[claim]
text = """{claim}"""
context = {json.dumps(context_files)}

[result]
passed = {str(result.passed).lower()}
explanation = """{result.explanation}"""
'''
    cache_path.write_text(content)


def _generate_id() -> str:
    """Generate a short unique ID."""
    import secrets

    return secrets.token_hex(4)


# Module-level run ID, generated once per process
_run_id: str | None = None


def _get_run_id() -> str:
    """Get or generate the run ID for this process."""
    global _run_id
    if _run_id is None:
        _run_id = _generate_id()
    return _run_id


def _save_transcript(
    project_root: Path,
    concern_id: str,
    claim: str,
    context_files: list[str],
    prompt: str,
    system_prompt: str,
    response_content: str,
    result: VerificationResult,
) -> None:
    """Save a transcript of the LLM interaction as JSONL (pi-compatible format)."""
    transcripts_dir = project_root / ".certo" / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    # File name: {date}-verify-{run-id}.jsonl
    date_str = result.timestamp.strftime("%Y-%m-%d") if result.timestamp else "unknown"
    run_id = _get_run_id()
    transcript_path = transcripts_dir / f"{date_str}-verify-{run_id}.jsonl"
    timestamp = result.timestamp.isoformat() if result.timestamp else None

    # Generate IDs for linking
    user_id = _generate_id()
    assistant_id = _generate_id()

    # User message (the verification request)
    user_entry = {
        "type": "message",
        "id": user_id,
        "parentId": None,
        "timestamp": timestamp,
        "message": {
            "role": "user",
            "content": [
                {"type": "text", "text": f"[certo verify] {concern_id}: {claim}"},
                {"type": "text", "text": prompt},
            ],
            "context": {
                "concern_id": concern_id,
                "claim": claim,
                "context_files": context_files,
                "system_prompt": system_prompt,
            },
        },
    }

    # Assistant message (the response)
    assistant_entry = {
        "type": "message",
        "id": assistant_id,
        "parentId": user_id,
        "timestamp": timestamp,
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": response_content}],
            "provider": "openrouter",
            "model": result.model,
            "usage": {
                "input": result.prompt_tokens,
                "output": result.completion_tokens,
                "totalTokens": result.total_tokens,
                "cost": {
                    "total": result.cost,
                },
            },
            "result": {
                "passed": result.passed,
                "explanation": result.explanation,
            },
        },
    }

    # Append to JSONL file
    with open(transcript_path, "a") as f:
        f.write(json.dumps(user_entry) + "\n")
        f.write(json.dumps(assistant_entry) + "\n")


def verify_concern(
    concern_id: str,
    claim: str,
    context_patterns: list[str],
    project_root: Path,
    *,
    model: str | None = None,
    no_cache: bool = False,
) -> VerificationResult:
    """Verify a concern using LLM.

    Args:
        concern_id: ID of the concern being verified.
        claim: The claim to verify.
        context_patterns: Glob patterns for context files.
        project_root: Root of the project.
        model: Optional model override.
        no_cache: If True, skip cache lookup.

    Returns:
        VerificationResult with pass/fail and explanation.

    Raises:
        FileMissingError: If context files are missing.
        FileTooLargeError: If context files are too large.
        LLMError: If the LLM call fails.
    """
    # Load context files
    context_contents, resolved_files = _load_context(context_patterns, project_root)
    context_file_list = [str(f.relative_to(project_root)) for f in resolved_files]

    # Check cache
    cache_key = _hash_inputs(claim, context_contents)
    cache_path = _get_cache_path(project_root, cache_key, concern_id)

    if not no_cache:
        cached = _load_cached_result(cache_path)
        if cached and cached.cache_key == cache_key:
            return cached

    # Build prompt and call LLM
    prompt = _build_prompt(claim, context_contents)
    response: LLMResponse = call_llm(
        prompt,
        system=VERIFY_SYSTEM_PROMPT,
        model=model,
        task="check",
        json_response=True,
    )

    # Parse response - try to extract JSON from the response
    # Some models return JSON embedded in text despite json_response=True
    import re

    result_data = None
    content = response.content.strip()

    # First try direct parse
    try:
        result_data = json.loads(content)
    except json.JSONDecodeError:
        # Try to find JSON object in the response (greedy match for nested braces)
        json_match = re.search(
            r'\{"pass":\s*(true|false),\s*"explanation":\s*"[^"]*"\}', content
        )
        if json_match:
            try:
                result_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

    if result_data is not None and "pass" in result_data:
        passed = bool(result_data.get("pass", False))
        explanation = str(result_data.get("explanation", ""))
    else:
        # If JSON parsing fails, treat as failure
        passed = False
        explanation = f"Failed to parse LLM response: {content[:200]}"

    result = VerificationResult(
        passed=passed,
        explanation=explanation,
        model=response.model,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        total_tokens=response.total_tokens,
        cost=response.cost,
        cached=False,
        cache_key=cache_key,
        timestamp=datetime.now(timezone.utc),
    )

    # Save to cache
    _save_cached_result(cache_path, result, concern_id, claim, context_file_list)

    # Save transcript for audit trail
    _save_transcript(
        project_root=project_root,
        concern_id=concern_id,
        claim=claim,
        context_files=context_file_list,
        prompt=prompt,
        system_prompt=VERIFY_SYSTEM_PROMPT,
        response_content=response.content,
        result=result,
    )

    return result
