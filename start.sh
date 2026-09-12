#!/bin/sh
set -e
alembic upgrade head
python -m scripts.bootstrap_demo_clinic
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
