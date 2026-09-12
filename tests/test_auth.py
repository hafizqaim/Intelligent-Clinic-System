"""Tests for /api/auth endpoints — register, login, /me."""

import httpx

from tests.conftest import (
    CLINIC_A_ID,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
)


# ── Registration ──────────────────────────────────────────────────────────────


class TestRegister:
    async def test_register_new_user(self, client_anon: httpx.AsyncClient):
        r = await client_anon.post(
            "/api/auth/register",
            json={
                "email": "newuser@phase6test.com",
                "password": "Secure123!",
                "full_name": "New User",
                "role": "user",
                "clinic_id": CLINIC_A_ID,
            },
        )
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == "newuser@phase6test.com"
        assert body["full_name"] == "New User"
        assert body["role"] == "user"
        assert "id" in body

    async def test_register_duplicate_email(self, client_anon: httpx.AsyncClient):
        r = await client_anon.post(
            "/api/auth/register",
            json={
                "email": ADMIN_EMAIL,
                "password": "x",
                "full_name": "Dup",
                "role": "user",
                "clinic_id": CLINIC_A_ID,
            },
        )
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"].lower()

    async def test_register_invalid_email(self, client_anon: httpx.AsyncClient):
        r = await client_anon.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "x",
                "full_name": "Bad",
                "role": "user",
                "clinic_id": CLINIC_A_ID,
            },
        )
        assert r.status_code == 422  # Pydantic validation


# ── Login ─────────────────────────────────────────────────────────────────────


class TestLogin:
    async def test_login_success(self, client_anon: httpx.AsyncClient):
        r = await client_anon.post(
            "/api/auth/login",
            data={
                "username": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_login_wrong_password(self, client_anon: httpx.AsyncClient):
        r = await client_anon.post(
            "/api/auth/login",
            data={
                "username": ADMIN_EMAIL,
                "password": "TotallyWrong!",
            },
        )
        assert r.status_code == 401

    async def test_login_nonexistent_user(self, client_anon: httpx.AsyncClient):
        r = await client_anon.post(
            "/api/auth/login",
            data={
                "username": "ghost@nowhere.com",
                "password": "x",
            },
        )
        assert r.status_code == 401


# ── /me ───────────────────────────────────────────────────────────────────────


class TestMe:
    async def test_me_authenticated(self, client_admin: httpx.AsyncClient):
        r = await client_admin.get("/api/auth/me")
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == ADMIN_EMAIL
        assert body["role"] == "admin"

    async def test_me_unauthenticated(self, client_anon: httpx.AsyncClient):
        r = await client_anon.get("/api/auth/me")
        assert r.status_code == 401
