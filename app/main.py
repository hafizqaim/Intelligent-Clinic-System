"""FastAPI application factory with lifespan event for ML model loading."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
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

        # Ollama
        try:
            import httpx
            from app.core.config import settings

            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{settings.ollama_base_url}/api/tags")
                checks["ollama"] = "ok" if r.status_code == 200 else f"status {r.status_code}"
        except Exception:
            checks["ollama"] = "unreachable"

        overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
        return {"status": overall, **checks}

    # Include routers
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry"])
    app.include_router(clinics.router, prefix="/api/clinics", tags=["clinics"])
    app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
    app.include_router(rag.router, prefix="/api/rag", tags=["rag"])

    return app


app = create_app()
