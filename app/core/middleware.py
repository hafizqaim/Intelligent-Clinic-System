"""ASGI middleware stack — CORS, request-ID tracing, global error handling."""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import structlog

log = structlog.get_logger(__name__)


# ── Request ID middleware ─────────────────────────────────────────────────────

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a unique X-Request-ID header into every request/response and bind
    it to the structlog context so all downstream log lines include it."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ── Global exception handler middleware ───────────────────────────────────────

class ExceptionMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return a consistent 500 JSON body."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception:
            log.exception("unhandled_exception", path=str(request.url.path))
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )


# ── Register all middleware on the app ────────────────────────────────────────

def register_middleware(app: FastAPI) -> None:
    """Attach the middleware stack.  Order matters — outermost is added last."""
    # CORS (outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID
    app.add_middleware(RequestIDMiddleware)

    # Global exception handler (innermost)
    app.add_middleware(ExceptionMiddleware)
