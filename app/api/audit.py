"""Audit router. Admin + auditor (CONTEXT specifics)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_permission
from app.domain import AuditEntryOut
from app.services.audit_service import list_paginated

router = APIRouter(tags=["audit"])


@router.get(
    "/audit",
    response_model=list[AuditEntryOut],
    dependencies=[Depends(require_permission("/audit", "GET"))],
)
async def get_audit(
    session: DbSession,
    _user: CurrentUser,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AuditEntryOut]:
    return list(await list_paginated(session, offset=offset, limit=limit))
