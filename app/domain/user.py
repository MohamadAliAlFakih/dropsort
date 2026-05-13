"""User domain models (DTOs distinct from ORM per API-05)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

Role = Literal["admin", "reviewer", "auditor"]


class UserOut(BaseModel):
    """Returned from /me and /admin/users/*. NEVER includes hashed_password (week-4)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    """POST /admin/users/invite body."""

    email: EmailStr
    password: str  # admin sets initial password; user changes after first login
    role: Role


class RoleChangeIn(BaseModel):
    """POST /admin/users/{id}/role body."""

    role: Role
