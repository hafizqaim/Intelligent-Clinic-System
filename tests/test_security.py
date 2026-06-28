"""Security-focused tests — auth enforcement, invalid tokens, health check."""
import pytest
import httpx
from jose import jwt


# ── Unauthenticated access should be blocked on protected endpoints ──────────

PROTECTED_ENDPOINTS = [
    ("GET",  "/api/auth/me"),
    ("GET",  "/api/clinics/"),
    ("POST", "/api/clinics/"),
    ("GET",  "/api/patients/"),
    ("POST", "/api/patients/"),
    ("POST", "/api/telemetry/ingest"),
    ("GET",  "/api/telemetry/readings?patient_id=00000000-0000-0000-0000-000000000000"),
    ("GET",  "/api/telemetry/anomalies?patient_id=00000000-0000-0000-0000-000000000000"),
]


class TestUnauthenticatedAccess:
    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    async def test_protected_returns_401(
        self, client_anon: httpx.AsyncClient, method: str, path: str
    ):
        r = await client_anon.request(method, path)
        assert r.status_code == 401


# ── Invalid / tampered tokens ────────────────────────────────────────────────

class TestInvalidTokens:
    async def test_garbage_token(self, client_anon: httpx.AsyncClient):
        r = await client_anon.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer totalgarbage"},
        )
        assert r.status_code == 401

    async def test_token_signed_with_wrong_key(self, client_anon: httpx.AsyncClient):
        bad_token = jwt.encode(
            {"sub": "00000000-0000-0000-0000-000000000000", "role": "admin", "clinic_id": "x"},
            "wrong-secret",
            algorithm="HS256",
        )
        r = await client_anon.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        assert r.status_code == 401

    async def test_expired_token(self, client_anon: httpx.AsyncClient):
        from datetime import datetime, timedelta, timezone

        expired = jwt.encode(
            {
                "sub": "00000000-0000-0000-0000-000000000000",
                "role": "admin",
                "clinic_id": "x",
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            },
            "your_secret_key_here",  # matches .env SECRET_KEY
            algorithm="HS256",
        )
        r = await client_anon.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert r.status_code == 401


# ── Health check (public) ────────────────────────────────────────────────────

class TestHealthCheck:
    async def test_health_no_auth_required(self, client_anon: httpx.AsyncClient):
        r = await client_anon.get("/health")
        assert r.status_code == 200

    async def test_health_deep_check_fields(self, client_anon: httpx.AsyncClient):
        r = await client_anon.get("/health")
        body = r.json()
        assert "status" in body
        assert "database" in body
        assert "ml_model" in body
        assert body["database"] == "ok"
        assert body["ml_model"] == "ok"


# ── RBAC enforcement ─────────────────────────────────────────────────────────

ADMIN_ONLY_ENDPOINTS = [
    ("POST", "/api/clinics/", {"name": "X", "address": "X", "phone_number": "X"}),
]


class TestRBAC:
    async def test_doctor_cannot_create_clinic(self, client_doctor: httpx.AsyncClient):
        """Clinic creation requires admin role."""
        r = await client_doctor.post("/api/clinics/", json={
            "name": "Forbidden",
            "address": "No",
            "phone_number": "000",
        })
        assert r.status_code == 403
        assert "permissions" in r.json()["detail"].lower()

    async def test_admin_can_create_clinic(self, client_admin: httpx.AsyncClient):
        r = await client_admin.post("/api/clinics/", json={
            "name": "RBAC Admin Clinic",
            "address": "OK",
            "phone_number": "111",
        })
        assert r.status_code == 201

    async def test_doctor_can_create_patient(self, client_doctor: httpx.AsyncClient):
        """Clinical staff (doctor) should be able to create patients."""
        r = await client_doctor.post("/api/patients/", json={
            "name": "RBAC Patient",
            "date_of_birth": "2000-01-01",
            "gender": "male",
            "medical_record_number": 999999,
        })
        assert r.status_code == 201

    async def test_response_has_request_id(self, client_anon: httpx.AsyncClient):
        """Every response should include the X-Request-ID header from middleware."""
        r = await client_anon.get("/health")
        assert "x-request-id" in r.headers
