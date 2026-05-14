"""Add users.deleted_at for soft-delete (audit FKs preserved).

Revision ID: 0003
Revises: 0002
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Adding nullable deleted_at so users can be soft-deleted without breaking audit_log FKs that reference users.id.
def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("deleted_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )


# Drop the column to reverse the soft-delete capability.
def downgrade() -> None:
    op.drop_column("users", "deleted_at")
