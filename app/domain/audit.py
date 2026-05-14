"""Audit log domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID
    actor_email: str | None = None
    action: str
    target_type: str
    target_id: str
    target_label: str | None = None
    created_at: datetime
    metadata_jsonb: dict[str, Any] | None
