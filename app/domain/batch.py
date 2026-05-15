"""Batch domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

BatchState = Literal["received", "processing", "complete", "failed"]


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_id: str | None
    state: BatchState
    created_at: datetime
    updated_at: datetime
    prediction_count: int = 0  # computed in repository
