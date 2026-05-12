"""Shared pytest fixtures. Phase 3+ extends with DB session, Vault client, RQ queue, etc."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """FastAPI TestClient. Context-manages lifespan so startup/shutdown hooks fire."""
    with TestClient(create_app()) as c:
        yield c
