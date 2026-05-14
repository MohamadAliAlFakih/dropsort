"""schema + casbin + admin seed

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-12

Creates 5 tables, seeds Casbin policies for admin/reviewer/auditor, seeds initial admin
user with password resolved from Vault path `secret/admin/initial_password`.

Per CONTEXT D-01 (Casbin policies via op.bulk_insert) and D-02 (admin via Vault).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Creates all 5 core tables, seeds Casbin RBAC policies, and inserts the initial admin user (password from Vault).
def upgrade() -> None:
    # 1) Tables
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(1024), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("is_superuser", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("role", sa.String(32), nullable=False, server_default="reviewer"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'reviewer', 'auditor')", name="ck_users_role"
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "casbin_rule",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ptype", sa.String(255), nullable=True),
        sa.Column("v0", sa.String(255), nullable=True),
        sa.Column("v1", sa.String(255), nullable=True),
        sa.Column("v2", sa.String(255), nullable=True),
        sa.Column("v3", sa.String(255), nullable=True),
        sa.Column("v4", sa.String(255), nullable=True),
        sa.Column("v5", sa.String(255), nullable=True),
    )

    op.create_table(
        "batches",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("external_id", sa.String(256), nullable=True, unique=True),
        sa.Column("state", sa.String(32), nullable=False, server_default="received"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "predictions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("minio_input_key", sa.String(1024), nullable=False),
        sa.Column("minio_overlay_key", sa.String(1024), nullable=True),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("top1_confidence", sa.Float, nullable=False),
        sa.Column("top5_json", postgresql.JSONB, nullable=False),
        sa.Column("relabel_label", sa.String(64), nullable=True),
        sa.Column(
            "relabel_actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("relabel_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_predictions_batch_id", "predictions", ["batch_id"])
    op.create_index(
        "ix_predictions_content_sha256", "predictions", ["content_sha256"], unique=True
    )

    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("metadata_jsonb", postgresql.JSONB, nullable=True),
    )
    op.create_index(
        "ix_audit_actor_created",
        "audit_log",
        ["actor_id", sa.text("created_at DESC")],
    )
    op.create_index("ix_audit_target", "audit_log", ["target_type", "target_id"])

    # 2) Casbin policies (CONTEXT specifics)
    policies = [
        # admin: full access
        {"ptype": "p", "v0": "admin", "v1": "/admin/*", "v2": "GET"},
        {"ptype": "p", "v0": "admin", "v1": "/admin/*", "v2": "POST"},
        {"ptype": "p", "v0": "admin", "v1": "/admin/*", "v2": "PATCH"},
        {"ptype": "p", "v0": "admin", "v1": "/admin/*", "v2": "DELETE"},
        {"ptype": "p", "v0": "admin", "v1": "/audit", "v2": "GET"},
        {"ptype": "p", "v0": "admin", "v1": "/batches", "v2": "GET"},
        {"ptype": "p", "v0": "admin", "v1": "/batches/*", "v2": "GET"},
        {"ptype": "p", "v0": "admin", "v1": "/predictions/*", "v2": "GET"},
        {"ptype": "p", "v0": "admin", "v1": "/me", "v2": "GET"},
        # reviewer: read batches/predictions, relabel (service enforces top1 < 0.7)
        {"ptype": "p", "v0": "reviewer", "v1": "/me", "v2": "GET"},
        {"ptype": "p", "v0": "reviewer", "v1": "/batches", "v2": "GET"},
        {"ptype": "p", "v0": "reviewer", "v1": "/batches/*", "v2": "GET"},
        {"ptype": "p", "v0": "reviewer", "v1": "/predictions/recent", "v2": "GET"},
        {"ptype": "p", "v0": "reviewer", "v1": "/predictions/*", "v2": "PATCH"},
        # auditor: read batches + audit only
        {"ptype": "p", "v0": "auditor", "v1": "/me", "v2": "GET"},
        {"ptype": "p", "v0": "auditor", "v1": "/batches", "v2": "GET"},
        {"ptype": "p", "v0": "auditor", "v1": "/batches/*", "v2": "GET"},
        {"ptype": "p", "v0": "auditor", "v1": "/audit", "v2": "GET"},
    ]
    casbin_rule = sa.table(
        "casbin_rule",
        sa.column("ptype", sa.String),
        sa.column("v0", sa.String),
        sa.column("v1", sa.String),
        sa.column("v2", sa.String),
    )
    op.bulk_insert(casbin_rule, policies)

    # 3) Initial admin user
    admin_password = _resolve_admin_password_from_vault()
    hashed = _hash_password(admin_password)

    users = sa.table(
        "users",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("email", sa.String),
        sa.column("hashed_password", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("is_superuser", sa.Boolean),
        sa.column("is_verified", sa.Boolean),
        sa.column("role", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        users,
        [
            {
                "id": uuid4(),
                "email": "admin@example.com",
                "hashed_password": hashed,
                "is_active": True,
                "is_superuser": False,
                "is_verified": True,
                "role": "admin",
                "created_at": datetime.now(tz=timezone.utc),
            }
        ],
    )


# Drops everything 0002 created, in reverse order, so audit FKs unwind before their target tables disappear.
def downgrade() -> None:
    op.drop_index("ix_audit_target", table_name="audit_log")
    op.drop_index("ix_audit_actor_created", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("ix_predictions_content_sha256", table_name="predictions")
    op.drop_index("ix_predictions_batch_id", table_name="predictions")
    op.drop_table("predictions")
    op.drop_table("batches")
    op.drop_table("casbin_rule")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")


# ----- Helpers (kept local to revision so the migration is self-contained) -----


# Reads admin bootstrap password from Vault (with env override for CI) so the secret never lives in source or .env.
def _resolve_admin_password_from_vault() -> str:
    """Read `secret/admin/initial_password` from Vault. Falls back to env var for tests/CI."""
    env_override = os.environ.get("ADMIN_INITIAL_PASSWORD")
    if env_override:
        return env_override

    import hvac

    vault_addr = os.environ.get("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.environ.get("VAULT_DEV_ROOT_TOKEN", "dropsort-dev-token")
    client = hvac.Client(url=vault_addr, token=vault_token)
    response = client.secrets.kv.v2.read_secret_version(path="admin/initial_password")
    return response["data"]["data"]["value"]


# Argon2-hashes the password using the same scheme fastapi-users uses, so the seeded admin can log in via the normal auth flow.
def _hash_password(plain: str) -> str:
    """Argon2 hash matching fastapi-users default."""
    from passlib.context import CryptContext

    ctx = CryptContext(schemes=["argon2"], deprecated="auto")
    return ctx.hash(plain)
