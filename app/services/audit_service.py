"""Audit service - read-only. Writes happen in other services' transactions."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import AuditEntryOut
from app.repositories import audit_repository


async def list_paginated(
    session: AsyncSession, offset: int = 0, limit: int = 50
) -> Sequence[AuditEntryOut]:
    return await audit_repository.list_paginated(session, offset=offset, limit=limit)
