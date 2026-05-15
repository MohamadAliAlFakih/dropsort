"""Predictions router."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_cache.decorator import cache

from app.api.deps import CurrentUser, DbSession, require_permission
from app.domain import PredictionOut, PredictionRelabelIn
from app.services.prediction_service import (
    PredictionNotFound,
    RelabelNotAllowed,
    list_recent,
    relabel,
)

router = APIRouter(tags=["predictions"])


@router.get(
    "/predictions/recent",
    response_model=list[PredictionOut],
    dependencies=[Depends(require_permission("/predictions/recent", "GET"))],
)
@cache(expire=15, namespace="predictions-recent")
async def list_recent_endpoint(
    session: DbSession,
    _user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[PredictionOut]:
    return list(await list_recent(session, limit=limit))


@router.patch(
    "/predictions/{prediction_id}",
    response_model=PredictionOut,
    dependencies=[Depends(require_permission("/predictions/{prediction_id}", "PATCH"))],
)
async def relabel_endpoint(
    session: DbSession,
    user: CurrentUser,
    prediction_id: UUID,
    body: PredictionRelabelIn,
) -> PredictionOut:
    try:
        return await relabel(
            session=session,
            pid=prediction_id,
            new_label=body.label,
            actor_id=user.id,
        )
    except PredictionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found"
        ) from None
    except RelabelNotAllowed as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot relabel: confidence {exc.top1:.4f} is above threshold 0.7"
            ),
        ) from None
