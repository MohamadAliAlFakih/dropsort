"""Prediction domain model - cross-track contract per CONTEXT D-03.

Saleh's Phase 2 `classify(image_bytes) -> Prediction` returns this.
Nasser's Phase 4 worker passes this to `prediction_service.record_prediction(...)`.
Phase 3's API response_model uses `PredictionOut` which embeds these fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TopKItem(BaseModel):
    """One entry in the top-5 list - label + softmax score."""

    label: str
    score: Annotated[float, Field(ge=0.0, le=1.0)]


class Prediction(BaseModel):
    """The classifier's verdict on a single image.

    `top5` is ordered descending by score; len == 5; top5[0].label == label and
    top5[0].score == top1_confidence (by construction).
    """

    label: str
    top1_confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    top5: Annotated[list[TopKItem], Field(min_length=5, max_length=5)]


class PredictionOut(BaseModel):
    """What the API returns to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_id: UUID
    filename: str
    label: str
    top1_confidence: float
    top5: list[TopKItem]
    minio_overlay_key: str | None
    relabel_label: str | None
    relabel_actor_id: UUID | None
    relabel_at: datetime | None
    created_at: datetime


class PredictionRelabelIn(BaseModel):
    """Request body for PATCH /predictions/{pid}. Reviewer-only; service rejects if top1 >= 0.7."""

    label: str
