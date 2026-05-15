"""Casbin: PATCH /predictions/* for admin (so admins can also relabel).

Revision ID: 0007
Revises: 0006
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
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
            {"ptype": "p", "v0": "admin", "v1": "/predictions/*", "v2": "PATCH"},
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM casbin_rule WHERE ptype = 'p' AND v0 = 'admin' "
            "AND v1 = '/predictions/*' AND v2 = 'PATCH'"
        )
    )
