"""Tests for /api/clinics endpoints — full CRUD."""

import httpx

from tests.conftest import CLINIC_A_ID


class TestCreateClinic:
    async def test_create_clinic(self, client_admin: httpx.AsyncClient):
        r = await client_admin.post(
            "/api/clinics/",
            json={
                "name": "Phase6 Clinic",
                "address": "123 Test St",
                "phone_number": "555-0006",
            },
        )
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Phase6 Clinic"
        assert "id" in body

    async def test_create_clinic_unauthenticated(self, client_anon: httpx.AsyncClient):
        r = await client_anon.post(
            "/api/clinics/",
            json={
                "name": "Bad",
            },
        )
        assert r.status_code == 401


class TestListClinics:
    async def test_list_clinics(self, client_admin: httpx.AsyncClient):
        r = await client_admin.get("/api/clinics/")
        assert r.status_code == 200
        clinics = r.json()
        assert isinstance(clinics, list)
        assert len(clinics) >= 2  # Clinic A + Clinic B from seed

    async def test_list_clinics_unauthenticated(self, client_anon: httpx.AsyncClient):
        r = await client_anon.get("/api/clinics/")
        assert r.status_code == 401


class TestGetClinic:
    async def test_get_clinic_by_id(self, client_admin: httpx.AsyncClient):
        r = await client_admin.get(f"/api/clinics/{CLINIC_A_ID}")
        assert r.status_code == 200
        assert r.json()["name"] == "Clinic A"

    async def test_get_clinic_not_found(self, client_admin: httpx.AsyncClient):
        r = await client_admin.get("/api/clinics/00000000-dead-dead-dead-deaddeaddead")
        assert r.status_code == 404


class TestGetMyClinic:
    async def test_get_my_clinic(self, client_admin: httpx.AsyncClient):
        r = await client_admin.get("/api/clinics/me")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == CLINIC_A_ID


class TestUpdateClinic:
    async def test_update_clinic(self, client_admin: httpx.AsyncClient):
        r = await client_admin.put(
            f"/api/clinics/{CLINIC_A_ID}",
            json={
                "phone_number": "555-9999",
            },
        )
        assert r.status_code == 200
        assert r.json()["phone_number"] == "555-9999"

    async def test_update_clinic_not_found(self, client_admin: httpx.AsyncClient):
        r = await client_admin.put(
            "/api/clinics/00000000-dead-dead-dead-deaddeaddead",
            json={"phone_number": "x"},
        )
        assert r.status_code == 404


class TestDeleteClinic:
    async def test_delete_clinic(self, client_admin: httpx.AsyncClient):
        # Create a throwaway clinic then delete it
        cr = await client_admin.post(
            "/api/clinics/",
            json={
                "name": "ToDelete",
                "address": "Nowhere",
                "phone_number": "000",
            },
        )
        cid = cr.json()["id"]
        r = await client_admin.delete(f"/api/clinics/{cid}")
        assert r.status_code == 204

        # Confirm it's gone
        r2 = await client_admin.get(f"/api/clinics/{cid}")
        assert r2.status_code == 404

    async def test_delete_clinic_not_found(self, client_admin: httpx.AsyncClient):
        r = await client_admin.delete(
            "/api/clinics/00000000-dead-dead-dead-deaddeaddead"
        )
        assert r.status_code == 404
