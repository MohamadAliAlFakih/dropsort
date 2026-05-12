"""Error envelope (LOG-04).

Every error response on every endpoint takes the shape:
  { "error": { "code": str, "message": str, "request_id": str | None } }

Stack traces are emitted to logs only - never in the response body (week-2/week-4 lessons).
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.request_id import get_current_request_id

logger = structlog.get_logger(__name__)


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


def _envelope(code: str, message: str, status_code: int) -> JSONResponse:
    body = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            request_id=get_current_request_id(),
        )
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Wire all error responses through ErrorEnvelope. Phase 3 adds domain-specific handlers."""

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return _envelope(
            code=f"http_{exc.status_code}",
            message=str(exc.detail),
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _envelope(
            code="request_validation_error",
            message="Invalid request payload",
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        return _envelope(
            code="internal_error",
            message="Internal server error",
            status_code=500,
        )
