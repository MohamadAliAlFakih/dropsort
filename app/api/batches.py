"""Batches router. GET /batches, POST /batches/upload, GET /batches/{batch_id}."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi_cache.decorator import cache
from pydantic import BaseModel

from app.api.deps import CurrentUser, DbSession, require_permission
from app.domain import BatchOut, PredictionOut
from app.services.batch_service import BatchNotFound, get_batch, list_batches
from app.services.batch_upload_service import UploadRejected, enqueue_browser_tiff

router = APIRouter(tags=["batches"])


class BatchDetail(BaseModel):
    batch: BatchOut
    predictions: list[PredictionOut]


class BatchUploadAccepted(BaseModel):
    """POST /batches/upload — same pipeline as SFTP; worker calls `record_prediction`."""

    batch: BatchOut
    job_id: str


@router.post(
    "/batches/upload",
    response_model=BatchUploadAccepted,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("/batches/upload", "POST"))],
)
async def upload_batch_tiff(
    session: DbSession,
    _user: CurrentUser,
    file: UploadFile = File(..., description="Single TIFF document (.tif / .tiff)."),
) -> BatchUploadAccepted:
    raw_name = file.filename
    try:
        body = await file.read()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read upload body."
        ) from exc

    try:
        batch, job_id = await enqueue_browser_tiff(
            session, file_bytes=body, filename=raw_name or ""
        )
    except UploadRejected as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.reason,
        ) from exc

    return BatchUploadAccepted(batch=batch, job_id=job_id)


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
    """Build Redis key compatible with `FastAPICache.clear(namespace=f"batches-detail:{id}")`.

    `clear()` expands to prefix `dropsort-cache:batches-detail:{uuid}` then deletes
    `KEYS {that}:*`. The stored key must therefore extend that prefix with a non-empty
    suffix (e.g. `:detail`); a bare `batches-detail:{uuid}` was never matched.
    """
    kwargs = kwargs or {}
    batch_id = kwargs["batch_id"]
    return f"{namespace}:{batch_id}:detail"


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
