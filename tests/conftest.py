"""Shared pytest fixtures.

Tests need compose Redis + Postgres + Vault running. Run:
  docker compose up -d db redis vault
  export ADMIN_INITIAL_PASSWORD=test-admin-pw
  export VAULT_ADDR=http://localhost:8200
  uv run alembic upgrade head
  uv run pytest

Test architecture:
- pytest-asyncio in auto mode: every `async def test_*` runs in its own event loop.
- asgi_lifespan.LifespanManager: drives FastAPI lifespan startup/shutdown around each
  test, so secrets/DB/Redis/Casbin are re-initialized per test.
- httpx.AsyncClient with ASGITransport: in-process calls into the app on the test's
  own loop - avoids TestClient's sync-loop adapter that leaked asyncpg connections
  across tests in the earlier setup.
"""

from __future__ import annotations

import os
import socket
import subprocess
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import create_app


def _port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except OSError:
        return False


@pytest.fixture(scope="session", autouse=True)
def _require_stack() -> None:
    """Skip the whole session if compose stack isn't up."""
    missing = []
    if not _port_open("127.0.0.1", 5432):
        missing.append("postgres:5432")
    if not _port_open("127.0.0.1", 6379):
        missing.append("redis:6379")
    if not _port_open("127.0.0.1", 8200):
        missing.append("vault:8200")
    if missing:
        pytest.skip(
            f"Compose stack not running. Missing: {missing}. "
            "Run: docker compose up -d db redis vault && alembic upgrade head"
        )

    os.environ.setdefault("VAULT_ADDR", "http://localhost:8200")
    os.environ.setdefault("ADMIN_INITIAL_PASSWORD", "test-admin-pw")
    os.environ.setdefault("DROPSORT_DB_NULL_POOL", "1")


@pytest.fixture(autouse=True)
def _reset_cache_and_redis_before_test() -> None:
    """Before each test:
    1. FLUSHALL Redis (so rate-limit counters + cached entries don't bleed across).
    2. Reset FastAPICache._init so the next lifespan's `FastAPICache.init(...)` actually
       binds the fresh redis client. Without this, fastapi-cache2 returns early from
       init() on the 2nd call and keeps a stale backend bound to the 1st test's
       (now-closed) event loop -> `RuntimeError: Event loop is closed` on every test
       that touches the cache.
    """
    from fastapi_cache import FastAPICache

    subprocess.run(
        ["docker", "exec", "dropsort-redis-1", "redis-cli", "FLUSHALL"],
        capture_output=True,
        check=False,
    )
    FastAPICache._init = False


@pytest_asyncio.fixture()
async def client() -> AsyncIterator[AsyncClient]:
    """Async HTTP client wired to a freshly-built app via ASGI transport.

    LifespanManager runs startup (Vault/DB/Redis/Casbin) before the test and shutdown
    after. Each test gets its own app + own engines bound to its own event loop.
    """
    app = create_app()
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as ac:
            yield ac


@pytest_asyncio.fixture()
async def admin_token(client: AsyncClient) -> str:
    pw = os.environ.get("ADMIN_INITIAL_PASSWORD", "test-admin-pw")
    response = await client.post(
        "/auth/jwt/login",
        data={"username": "admin@example.com", "password": pw},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


async def _invite_and_login(
    client: AsyncClient, admin_token: str, email: str, password: str, role: str
) -> str:
    """Idempotent invite-or-set-role + login. The earlier session may have created the
    user with a different role; we re-bind role if needed before logging in.
    """
    auth = {"Authorization": f"Bearer {admin_token}"}
    # Invite (ignore the 409 conflict that means the user pre-exists)
    await client.post(
        "/admin/users/invite",
        headers=auth,
        json={"email": email, "initial_secret": password, "role": role},
    )
    users = (await client.get("/admin/users", headers=auth)).json()
    target = next((u for u in users if u["email"] == email), None)
    if target is not None and target["role"] != role:
        await client.post(
            f"/admin/users/{target['id']}/role",
            headers=auth,
            json={"role": role},
        )
    resp = await client.post(
        "/auth/jwt/login", data={"username": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture()
async def reviewer_token(client: AsyncClient, admin_token: str) -> str:
    return await _invite_and_login(
        client, admin_token, "rev@example.com", "rev-pw-1234", "reviewer"
    )


@pytest_asyncio.fixture()
async def auditor_token(client: AsyncClient, admin_token: str) -> str:
    return await _invite_and_login(
        client, admin_token, "aud@example.com", "aud-pw-1234", "auditor"
    )
