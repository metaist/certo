"""Spec verification checks."""

from __future__ import annotations

from certo.check.core import CheckContext, CheckResult, check_spec
from certo.check.static import check_spec_exists, check_spec_valid_toml

# Backward compatibility aliases
check_blueprint = check_spec
check_blueprint_exists = check_spec_exists
check_blueprint_valid_toml = check_spec_valid_toml

__all__ = [
    "CheckContext",
    "CheckResult",
    "check_spec",
    "check_spec_exists",
    "check_spec_valid_toml",
    # Backward compatibility
    "check_blueprint",
    "check_blueprint_exists",
    "check_blueprint_valid_toml",
]
