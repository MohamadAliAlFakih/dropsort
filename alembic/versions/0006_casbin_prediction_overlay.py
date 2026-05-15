"""Casbin: GET /predictions/*/overlay for admin + reviewer (browser image preview).

Revision ID: 0006
Revises: 0005
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
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
            {"ptype": "p", "v0": "admin", "v1": "/predictions/*/overlay", "v2": "GET"},
            {"ptype": "p", "v0": "reviewer", "v1": "/predictions/*/overlay", "v2": "GET"},
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM casbin_rule WHERE ptype = 'p' AND v1 = '/predictions/*/overlay' "
            "AND v2 = 'GET' AND v0 IN ('admin', 'reviewer')"
        )
    )
