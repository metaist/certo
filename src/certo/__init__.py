"""Turn conversations into verifiable specifications."""

from __future__ import annotations


def __getattr__(name: str) -> str:
    """Lazy load version to avoid importlib.metadata overhead."""
    if name == "__version__":
        from importlib.metadata import version

        return version("certo")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
