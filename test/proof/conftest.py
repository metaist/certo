"""Proof infrastructure for formal verification with Z3.

Proofs are just tests with better coverage guarantees and aggressive caching.
They're marked with @pytest.mark.proof and can be skipped with -m "not proof".
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from z3 import Solver, sat, unsat

# Cache directory for proof results
PROOF_CACHE_DIR = Path(__file__).parent / ".proof_cache"


@dataclass
class ProofResult:
    """Result of running a formal proof."""

    name: str
    status: str  # "proved" | "failed" | "unknown" | "cached"
    message: str = ""
    counterexample: dict[str, Any] | None = None
    duration_ms: float = 0.0
    cached: bool = False


@dataclass
class ProofDependency:
    """Tracks source files a proof depends on."""

    files: list[str] = field(default_factory=list)

    def content_hash(self) -> str:
        """Hash the content of all dependency files."""
        hasher = hashlib.sha256()
        root = Path(__file__).parent.parent.parent  # project root

        for rel_path in sorted(self.files):
            path = root / rel_path
            if path.exists():
                hasher.update(rel_path.encode())
                hasher.update(path.read_bytes())

        return hasher.hexdigest()[:16]


@dataclass
class ProofCache:
    """Cache entry for a proof result."""

    name: str
    dependency_hash: str
    status: str
    message: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "dependency_hash": self.dependency_hash,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProofCache:
        return cls(
            name=data["name"],
            dependency_hash=data["dependency_hash"],
            status=data["status"],
            message=data.get("message", ""),
            timestamp=data.get("timestamp", ""),
        )

    def save(self, cache_dir: Path) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{self.name}.json"
        cache_file.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, cache_dir: Path, name: str) -> ProofCache | None:
        cache_file = cache_dir / f"{name}.json"
        if not cache_file.exists():
            return None
        try:
            data = json.loads(cache_file.read_text())
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None


def check_cache(name: str, deps: ProofDependency) -> ProofResult | None:
    """Check if we have a valid cached result for this proof."""
    cached = ProofCache.load(PROOF_CACHE_DIR, name)
    if cached is None:
        return None

    current_hash = deps.content_hash()
    if cached.dependency_hash != current_hash:
        return None  # Dependencies changed, need to re-prove

    return ProofResult(
        name=name,
        status=cached.status,
        message=f"{cached.message} (cached)",
        cached=True,
    )


def save_cache(name: str, deps: ProofDependency, result: ProofResult) -> None:
    """Save proof result to cache."""
    cache = ProofCache(
        name=name,
        dependency_hash=deps.content_hash(),
        status=result.status,
        message=result.message,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    cache.save(PROOF_CACHE_DIR)


class ProofFailed(Exception):
    """Raised when a proof fails."""

    def __init__(self, result: ProofResult) -> None:
        self.result = result
        super().__init__(result.message)


def prove(
    solver: Solver,
    name: str,
    deps: list[str],
    timeout_ms: int = 30000,
    *,
    use_cache: bool = True,
) -> ProofResult:
    """Run a Z3 proof with caching.

    The solver should contain the NEGATION of what you want to prove.
    If unsat, the original claim is proved (no counterexample exists).

    Args:
        solver: Z3 Solver with negated claim
        name: Unique name for this proof (used for caching)
        deps: List of source files this proof depends on
        timeout_ms: Solver timeout in milliseconds
        use_cache: Whether to use cached results

    Returns:
        ProofResult with status and optional counterexample
    """
    dependency = ProofDependency(files=deps)

    # Check cache first
    if use_cache:
        cached_result = check_cache(name, dependency)
        if cached_result:
            return cached_result

    # Run the proof
    import time

    start = time.perf_counter()

    solver.set("timeout", timeout_ms)
    result = solver.check()

    duration_ms = (time.perf_counter() - start) * 1000

    proof_result: ProofResult
    match result:
        case _ if result == unsat:
            # UNSAT means no counterexample exists -> claim is PROVED
            proof_result = ProofResult(
                name=name,
                status="proved",
                message="proved (no counterexample exists)",
                duration_ms=duration_ms,
            )
        case _ if result == sat:
            # SAT means counterexample found -> claim is FALSE
            model = solver.model()
            counterexample = {str(d): str(model[d]) for d in model.decls()}
            proof_result = ProofResult(
                name=name,
                status="failed",
                message=f"counterexample found: {counterexample}",
                counterexample=counterexample,
                duration_ms=duration_ms,
            )
        # no cover: start
        case _:
            # UNKNOWN (timeout or undecidable) - hard to trigger reliably in tests
            proof_result = ProofResult(
                name=name,
                status="unknown",
                message=f"solver returned unknown (timeout={timeout_ms}ms)",
                duration_ms=duration_ms,
            )
        # no cover: stop

    # Cache the result
    if use_cache:
        save_cache(name, dependency, proof_result)

    return proof_result


def assert_proof(result: ProofResult) -> None:
    """Assert that a proof succeeded, raising ProofFailed if not."""
    if result.status == "proved":
        return
    raise ProofFailed(result)


# Register the proof marker with pytest
def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "proof: mark test as a formal Z3 proof")
