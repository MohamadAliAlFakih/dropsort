"""initial empty

Revision ID: 0001
Revises:
Create Date: 2026-05-11 00:00:00.000000

Phase 1 ships an intentionally empty initial migration per CONTEXT D-19.
Phase 3 (Fakih, API) adds revision 0002 with the real schema:
  - users (fastapi-users base + role column)
  - casbin_rule (Casbin SQLAlchemy adapter table)
  - batches
  - predictions (with content_sha256 UNIQUE for idempotency, PIPE-05)
  - audit_log

This empty revision exists so the `migrate` container in compose has SOMETHING to apply,
and so the DB-01 acceptance criterion ("alembic upgrade head + alembic downgrade base
both run cleanly") can be verified at the end of Phase 1.
"""

from __future__ import annotations

from typing import Sequence

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# No-op upgrade because Phase 1 needed a valid revision to test the migrate flow before real tables existed.
def upgrade() -> None:
    """Intentionally empty - see module docstring."""
    pass


# No-op downgrade so `alembic downgrade base` runs cleanly (DB-01 acceptance criterion).
def downgrade() -> None:
    """Intentionally empty - see module docstring."""
    pass
