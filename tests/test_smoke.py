"""Phase 1 smoke. Proves the bootstrap surface still imports under Phase 3 changes."""

from __future__ import annotations


def test_app_imports() -> None:
    """Phase 1 success crit #1: one trivial passing test."""
    from app.main import create_app

    app = create_app()
    assert app is not None
