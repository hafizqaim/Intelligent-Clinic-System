"""FastAPI application factory with lifespan event for ML model loading."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routers import auth, telemetry, clinics, patients, rag
from app.ml.predictor import detector
from app.database import SessionLocal
from app.core.logging import setup_logging, get_logger
from app.core.middleware import register_middleware

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Loads the ML model on startup, shuts down cleanly on exit.
    """
    json_logs = os.getenv("LOG_FORMAT", "console") == "json"
    setup_logging(json_output=json_logs, log_level=os.getenv("LOG_LEVEL", "INFO"))

    # Startup
    log.info("loading_ml_model")
    detector.load()
    log.info("ml_model_loaded")

    yield

    # Shutdown
    log.info("shutting_down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Intelligent Clinic System API",
        description="Multi-tenant healthcare platform with telemetry and RAG",
        version="1.0.0",
        lifespan=lifespan,
    )

    register_middleware(app)

    # ── Health check ──────────────────────────────────────────────────────
    @app.get("/health")
    async def health_check():
        checks: dict = {}

        # DB
        try:
            async with SessionLocal() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {exc}"

        # ML model
        checks["ml_model"] = "ok" if detector.model is not None else "not loaded"

        # LLM (Gemini) — checked for configuration only, not a live call, since
        # this endpoint is polled frequently and a live call would burn quota.
        from app.core.config import settings

        checks["llm"] = "ok" if settings.gemini_api_key else "not configured"

        overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
        return {"status": overall, **checks}

    # Include routers
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry"])
    app.include_router(clinics.router, prefix="/api/clinics", tags=["clinics"])
    app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
    app.include_router(rag.router, prefix="/api/rag", tags=["rag"])

    # Old bookmarked /ui links keep working, redirected to the new home.
    @app.get("/ui", include_in_schema=False)
    @app.get("/ui/", include_in_schema=False)
    async def redirect_old_ui_path():
        return RedirectResponse(url="/")

    # ── Web console (static SPA, same-origin so it can call the API directly) ──
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="ui")

    return app


app = create_app()
