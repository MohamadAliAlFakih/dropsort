"""Add users.original_email for friendly admin UI after soft-delete.

Revision ID: 0004
Revises: 0003
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("original_email", sa.String(length=320), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "original_email")
