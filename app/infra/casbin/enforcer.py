"""Casbin enforcer factory.

build_enforcer(sync_db_url) returns a sync Enforcer with the SQLAlchemy adapter.
Lifespan calls this once at boot. Reload after role change: user_service.change_role
calls enforcer.load_policy() after committing (CONTEXT D-07).

We use the sync Enforcer (not AsyncEnforcer) because casbin-sqlalchemy-adapter is
sync-only; AsyncEnforcer expects an async-adapter and rejects the SQLAlchemy one at
init. `enforce()` is pure CPU (matchers + model lookup); `load_policy()` does sync DB I/O
- service-layer callers wrap that single call in `asyncio.to_thread`.
"""

from __future__ import annotations

from pathlib import Path

from casbin import Enforcer
from casbin_sqlalchemy_adapter import Adapter

MODEL_CONF_PATH = Path(__file__).parent / "model.conf"


def build_enforcer(sync_db_url: str) -> Enforcer:
    """Build the sync enforcer. Pass a sync DB URL (psycopg2 driver, not asyncpg)."""
    adapter = Adapter(sync_db_url)
    enforcer = Enforcer(str(MODEL_CONF_PATH), adapter)
    return enforcer


def policy_row_count(sync_db_url: str) -> int:
    """For BOOT-02: count casbin_rule rows. If 0, api refuses to start."""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from app.db.models import CasbinRule

    engine = create_engine(sync_db_url)
    try:
        with Session(engine) as session:
            result = session.execute(select(CasbinRule))
            return len(result.scalars().all())
    finally:
        engine.dispose()
