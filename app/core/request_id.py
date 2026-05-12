"""Request-ID middleware (LOG-02, CONTEXT D-10 wiring).

Pure ASGI middleware. For each request:
- Echoes incoming `X-Request-ID` header if present.
- Otherwise generates a fresh UUID4.
- Binds the id into structlog's contextvars so every log line under this request carries it.
- Adds `X-Request-ID` to the response headers.

Phase 4 (Nasser, PIPE) extends this by writing the request_id into RQ job kwargs so the
inference worker's logs share the same id (LOG-03).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, MutableMapping

import structlog

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send

REQUEST_ID_HEADER = "x-request-id"
REQUEST_ID_HEADER_BYTES = REQUEST_ID_HEADER.encode("latin-1")


class RequestIdMiddleware:
    """ASGI middleware that ensures every request has a request_id."""

    def __init__(self, app: "ASGIApp") -> None:
        self.app = app

    async def __call__(
        self, scope: "Scope", receive: "Receive", send: "Send"
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id: str | None = None
        for header_name, header_value in scope.get("headers", []):
            if header_name == REQUEST_ID_HEADER_BYTES:
                request_id = header_value.decode("latin-1")
                break
        if not request_id:
            request_id = str(uuid.uuid4())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_with_request_id(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append(
                    (REQUEST_ID_HEADER_BYTES, request_id.encode("latin-1"))
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_request_id)


def get_current_request_id() -> str | None:
    """Look up the current request_id from structlog contextvars (None outside a request)."""
    ctx = structlog.contextvars.get_contextvars()
    value = ctx.get("request_id")
    return value if isinstance(value, str) else None
