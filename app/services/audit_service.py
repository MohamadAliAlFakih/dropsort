"""Audit service — reads audit rows and enriches them for human-facing clients."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import AuditEntryOut
from app.repositories import (
    audit_repository,
    batch_repository,
    prediction_repository,
    user_repository,
)


def _parse_uuid(value: str) -> UUID | None:
    try:
        return UUID(str(value))
    except (ValueError, AttributeError):
        return None


def _short(value: str, n: int = 12) -> str:
    t = value.strip()
    if len(t) <= n + 1:
        return t
    return t[:n] + "…"


async def _enrich(session: AsyncSession, rows: list[AuditEntryOut]) -> None:
    actor_ids = {r.actor_id for r in rows}
    actor_labels = await user_repository.map_user_display_labels(session, actor_ids)

    user_target_ids: set[UUID] = set()
    prediction_target_ids: set[UUID] = set()
    batch_target_ids: set[UUID] = set()
    for r in rows:
        tid = _parse_uuid(r.target_id)
        if tid is None:
            continue
        if r.target_type == "user":
            user_target_ids.add(tid)
        elif r.target_type == "prediction":
            prediction_target_ids.add(tid)
        elif r.target_type == "batch":
            batch_target_ids.add(tid)

    user_target_labels = await user_repository.map_user_display_labels(
        session, user_target_ids
    )
    pred_filenames = await prediction_repository.map_id_to_filename(
        session, prediction_target_ids
    )
    batch_labels = await batch_repository.map_id_to_display_label(session, batch_target_ids)

    for i, r in enumerate(rows):
        actor_email = actor_labels.get(r.actor_id)
        target_label: str | None = None
        tid = _parse_uuid(r.target_id)
        meta = r.metadata_jsonb or {}

        if r.target_type == "user":
            if tid is not None:
                target_label = user_target_labels.get(tid)
            if target_label is None and isinstance(meta.get("email"), str):
                target_label = meta["email"]
        elif r.target_type == "prediction" and tid is not None:
            fn = pred_filenames.get(tid)
            target_label = fn or _short(r.target_id)
        elif r.target_type == "batch" and tid is not None:
            base = batch_labels.get(tid)
            if base and isinstance(meta.get("filename"), str):
                target_label = f"{meta['filename']} · {base}"
            else:
                target_label = base
        elif tid is not None:
            target_label = _short(r.target_id)

        if target_label is None:
            target_label = _short(r.target_id)

        rows[i] = r.model_copy(
            update={
                "actor_email": actor_email,
                "target_label": target_label,
            }
        )


async def list_paginated(
    session: AsyncSession, offset: int = 0, limit: int = 50
) -> Sequence[AuditEntryOut]:
    rows = list(await audit_repository.list_paginated(session, offset=offset, limit=limit))
    await _enrich(session, rows)
    return rows
