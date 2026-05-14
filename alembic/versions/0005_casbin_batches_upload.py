"""Casbin: POST /batches/upload for admin + reviewer (browser TIFF ingestion).

Revision ID: 0005
Revises: 0004
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    casbin_rule = sa.table(
        "casbin_rule",
        sa.column("ptype", sa.String),
        sa.column("v0", sa.String),
        sa.column("v1", sa.String),
        sa.column("v2", sa.String),
    )
    op.bulk_insert(
        casbin_rule,
        [
            {"ptype": "p", "v0": "admin", "v1": "/batches/upload", "v2": "POST"},
            {"ptype": "p", "v0": "reviewer", "v1": "/batches/upload", "v2": "POST"},
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM casbin_rule WHERE ptype = 'p' AND v1 = '/batches/upload' "
            "AND v2 = 'POST' AND v0 IN ('admin', 'reviewer')"
        )
    )
