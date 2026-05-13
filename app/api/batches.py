"""Batches router. GET /batches + GET /batches/{batch_id}."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_cache.decorator import cache
from pydantic import BaseModel

from app.api.deps import CurrentUser, DbSession, require_permission
from app.domain import BatchOut, PredictionOut
from app.services.batch_service import BatchNotFound, get_batch, list_batches

router = APIRouter(tags=["batches"])


class BatchDetail(BaseModel):
    batch: BatchOut
    predictions: list[PredictionOut]


@router.get(
    "/batches",
    response_model=list[BatchOut],
    dependencies=[Depends(require_permission("/batches", "GET"))],
)
@cache(expire=30, namespace="batches-list")
async def list_batches_endpoint(
    session: DbSession,
    _user: CurrentUser,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[BatchOut]:
    return list(await list_batches(session, offset=offset, limit=limit))


def _batch_detail_key_builder(
    func: Any,
    namespace: str = "",
    *,
    request: Any = None,
    response: Any = None,
    args: Any = (),
    kwargs: Any = None,
) -> str:
    kwargs = kwargs or {}
    return f"batches-detail:{kwargs['batch_id']}"


@router.get(
    "/batches/{batch_id}",
    response_model=BatchDetail,
    dependencies=[Depends(require_permission("/batches/{batch_id}", "GET"))],
)
@cache(expire=30, namespace="batches-detail", key_builder=_batch_detail_key_builder)
async def get_batch_endpoint(
    session: DbSession,
    _user: CurrentUser,
    batch_id: UUID,
) -> BatchDetail:
    try:
        batch, preds = await get_batch(session, batch_id)
    except BatchNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found"
        ) from None
    return BatchDetail(batch=batch, predictions=list(preds))
