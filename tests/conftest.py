"""Shared fixtures for the Intelligent Clinic System test suite.

These are INTEGRATION tests that run against the real PostgreSQL database.
The test database is cleaned between test sessions via the ``clean_db`` fixture.
"""
import uuid
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport
from sqlalchemy import text

from app.main import app
from app.database import SessionLocal
from app.core.security import get_password_hash, create_access_token
from app.ml.predictor import detector


# ---------------------------------------------------------------------------
# Load ML model (normally done by app lifespan, which ASGITransport skips)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def _load_ml_model():
    detector.load()
    yield


# ---------------------------------------------------------------------------
# Database cleanup — runs once per session, wipes test artefacts
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def clean_db():
    """Delete all rows from mutable tables before the test run."""
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM telemetry_readings"))
        await session.execute(text("DELETE FROM chat_histories"))
        await session.execute(text("DELETE FROM document_embeddings"))
        await session.execute(text("DELETE FROM patients"))
        await session.execute(text("DELETE FROM users"))
        await session.execute(text("DELETE FROM clinics"))
        await session.commit()
    yield


# ---------------------------------------------------------------------------
# Seed data — deterministic UUIDs for reproducibility
# ---------------------------------------------------------------------------
CLINIC_A_ID = "00000000-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
CLINIC_B_ID = "00000000-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
ADMIN_ID = "11111111-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
DOCTOR_ID = "22222222-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
DOCTOR_B_ID = "22222222-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

ADMIN_EMAIL = "admin-test@clinica.com"
ADMIN_PASSWORD = "AdminPass123!"
DOCTOR_EMAIL = "doctor-test@clinica.com"
DOCTOR_PASSWORD = "DoctorPass123!"
DOCTOR_B_EMAIL = "doctor-test@clinicb.com"
DOCTOR_B_PASSWORD = "DoctorBPass123!"


@pytest_asyncio.fixture(scope="session")
async def seed(clean_db):
    """Insert two clinics + three users directly in the DB."""
    async with SessionLocal() as db:
        # Clinics
        await db.execute(
            text(
                "INSERT INTO clinics (id, name, address, phone_number, created_at) "
                "VALUES (:id, :name, :addr, :phone, NOW()) ON CONFLICT DO NOTHING"
            ),
            {"id": CLINIC_A_ID, "name": "Clinic A", "addr": "1 A St", "phone": "+111"},
        )
        await db.execute(
            text(
                "INSERT INTO clinics (id, name, address, phone_number, created_at) "
                "VALUES (:id, :name, :addr, :phone, NOW()) ON CONFLICT DO NOTHING"
            ),
            {"id": CLINIC_B_ID, "name": "Clinic B", "addr": "2 B St", "phone": "+222"},
        )

        # Users
        for uid, email, pw, role, cid in [
            (ADMIN_ID, ADMIN_EMAIL, ADMIN_PASSWORD, "admin", CLINIC_A_ID),
            (DOCTOR_ID, DOCTOR_EMAIL, DOCTOR_PASSWORD, "doctor", CLINIC_A_ID),
            (DOCTOR_B_ID, DOCTOR_B_EMAIL, DOCTOR_B_PASSWORD, "doctor", CLINIC_B_ID),
        ]:
            hashed = get_password_hash(pw)
            await db.execute(
                text(
                    "INSERT INTO users (id, clinic_id, email, hashed_password, full_name, role, is_active) "
                    "VALUES (CAST(:id AS uuid), CAST(:cid AS uuid), :email, :pw, :name, CAST(:role AS role), true) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"id": uid, "cid": cid, "email": email, "pw": hashed, "name": email.split("@")[0], "role": role},
            )
        await db.commit()
    yield


# ---------------------------------------------------------------------------
# HTTP clients — one per clinic tenant
# ---------------------------------------------------------------------------
def _make_token(user_id: str, role: str, clinic_id: str) -> str:
    return create_access_token(data={"sub": user_id, "role": role, "clinic_id": clinic_id})


@pytest_asyncio.fixture(scope="session")
async def client_admin(seed) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Authenticated HTTPX client for the admin of Clinic A."""
    token = _make_token(ADMIN_ID, "admin", CLINIC_A_ID)
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


@pytest_asyncio.fixture(scope="session")
async def client_doctor(seed) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Authenticated HTTPX client for the doctor of Clinic A."""
    token = _make_token(DOCTOR_ID, "doctor", CLINIC_A_ID)
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


@pytest_asyncio.fixture(scope="session")
async def client_doctor_b(seed) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Authenticated HTTPX client for the doctor of Clinic B."""
    token = _make_token(DOCTOR_B_ID, "doctor", CLINIC_B_ID)
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


@pytest_asyncio.fixture(scope="session")
async def client_anon(seed) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Unauthenticated HTTPX client."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
