"""Evidence types and verification logic."""

from __future__ import annotations

from certo.evidence.types import (
    Evidence,
    ShellEvidence,
    UrlEvidence,
    LlmEvidence,
    FactEvidence,
)
from certo.evidence.selector import parse_selector, resolve_selector
from certo.evidence.verify import Verify, verify_claim

__all__ = [
    "Evidence",
    "ShellEvidence",
    "UrlEvidence",
    "LlmEvidence",
    "FactEvidence",
    "Verify",
    "parse_selector",
    "resolve_selector",
    "verify_claim",
]
