"""Phase 1 smoke. Proves the bootstrap surface imports - nothing more.

Richer test coverage lands in Phase 3 (API) and Phase 5 (CI).
"""

from __future__ import annotations


def test_app_imports() -> None:
    """Phase 1 success crit #1: one trivial passing test."""
    from app.main import app

    assert app is not None
