"""Evidence types and verification logic."""

from __future__ import annotations

from certo.evidence.types import (
    AnyEvidence,
    Evidence,
    ShellEvidence,
    UrlEvidence,
    LlmEvidence,
    FactEvidence,
    load_evidence,
    save_evidence,
)
from certo.evidence.selector import parse_selector, resolve_selector
from certo.evidence.verify import Verify, verify_claim

__all__ = [
    "AnyEvidence",
    "Evidence",
    "ShellEvidence",
    "UrlEvidence",
    "LlmEvidence",
    "FactEvidence",
    "Verify",
    "load_evidence",
    "save_evidence",
    "parse_selector",
    "resolve_selector",
    "verify_claim",
]
