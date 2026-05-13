"""Casbin facade. Thin wrapper so other services don't import casbin directly."""

from __future__ import annotations

import asyncio
from typing import Any


def enforce(enforcer: Any, sub: str, obj: str, act: str) -> bool:
    return enforcer.enforce(sub, obj, act)


async def reload(enforcer: Any) -> None:
    """Reload policy from DB. Sync I/O wrapped in to_thread."""
    await asyncio.to_thread(enforcer.load_policy)
