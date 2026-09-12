# ── Build stage ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="Intelligent Clinic System"

# Non-root user for security
RUN groupadd -r clinic && useradd -r -g clinic -d /app -s /sbin/nologin clinic

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY ml_models/ ml_models/

# Own files by the non-root user
RUN chown -R clinic:clinic /app

USER clinic

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
