"""Auth tests (AUTH-01, AUTH-02, AUTH-03)."""

from __future__ import annotations

from httpx import AsyncClient


async def test_register_endpoint_does_not_exist(client: AsyncClient) -> None:
    """CONTEXT D-05: POST /auth/register intentionally absent."""
    r = await client.post("/auth/register", json={"email": "x@y.com", "password": "p"})
    assert r.status_code == 404


async def test_login_returns_jwt(client: AsyncClient, admin_token: str) -> None:
    assert isinstance(admin_token, str)
    assert len(admin_token) > 20


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    """AUTH-03: missing token -> 401."""
    r = await client.get("/me")
    assert r.status_code == 401


async def test_me_with_token_returns_user(
    client: AsyncClient, admin_token: str
) -> None:
    r = await client.get("/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == "admin@example.com"
    assert body["role"] == "admin"
    assert "hashed_password" not in body
