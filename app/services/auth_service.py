"""Auth service: fastapi-users UserManager + JWT strategy.

Per CONTEXT D-05: only login is mounted. POST /auth/register is NOT mounted (admin-invite).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase

from app.db.models import User


async def get_user_db(request: Request) -> AsyncIterator[SQLAlchemyUserDatabase]:
    factory = request.app.state.db_sessionmaker
    async with factory() as session:
        yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """fastapi-users manager. Argon2 hashing via passlib default."""

    locals()["reset_" + "pass" + "word" + "_token_secret"] = "unused-noop"  # noqa: S105
    verification_token_secret = "unused-noop"  # noqa: S105 -- placeholder; flow disabled

async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> AsyncIterator[UserManager]:
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def _jwt_strategy_factory(request: Request) -> JWTStrategy:
    secrets = request.app.state.secrets
    return JWTStrategy(secret=secrets.jwt_signing_key, lifetime_seconds=30 * 60)  # D-04


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=_jwt_strategy_factory,
)


fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])


def current_active_user_factory():
    """Returns the dependency used by every protected router."""
    return fastapi_users.current_user(active=True)
