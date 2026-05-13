"""SQLAlchemy ORM models.

DB-04: this is the ONLY module that defines SQLAlchemy ORM classes. Imported by:
- app/repositories/* (canonical consumer)
- app/services/auth_service.py (fastapi-users SQLAlchemyUserDatabase)
- app/api/deps.py (typing for CurrentUser)
- alembic/env.py (autogenerate target_metadata)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM classes."""


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User ORM. fastapi-users' SQLAlchemyBaseUserTableUUID provides:
      id (UUID pk), email, hashed_password, is_active, is_superuser, is_verified.
    We add: role + created_at + check constraint.
    """

    __tablename__ = "users"

    role: Mapped[str] = mapped_column(String(32), nullable=False, server_default="reviewer")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'reviewer', 'auditor')", name="ck_users_role"),
    )


class CasbinRule(Base):
    __tablename__ = "casbin_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ptype: Mapped[str | None] = mapped_column(String(255), nullable=True)
    v0: Mapped[str | None] = mapped_column(String(255), nullable=True)
    v1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    v2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    v3: Mapped[str | None] = mapped_column(String(255), nullable=True)
    v4: Mapped[str | None] = mapped_column(String(255), nullable=True)
    v5: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    external_id: Mapped[str | None] = mapped_column(String(256), nullable=True, unique=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, server_default="received")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_sha256: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    minio_input_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    minio_overlay_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    top1_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    top5_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    relabel_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    relabel_actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    relabel_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # `metadata` collides with Base.metadata - use a different attribute name.
    metadata_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_audit_actor_created", "actor_id", text("created_at DESC")),
        Index("ix_audit_target", "target_type", "target_id"),
    )
