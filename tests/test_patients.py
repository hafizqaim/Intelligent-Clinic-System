"""Tests for /api/patients endpoints — CRUD + RLS tenant isolation."""
import pytest
import httpx

from tests.conftest import CLINIC_A_ID, CLINIC_B_ID

RLS_XFAIL = pytest.mark.xfail(
    reason="DB user 'qaim' is a PostgreSQL superuser — RLS policies are bypassed",
    strict=False,
)


class TestCreatePatient:
    async def test_create_patient(self, client_doctor: httpx.AsyncClient):
        r = await client_doctor.post("/api/patients/", json={
            "name": "Alice Testpatient",
            "date_of_birth": "1990-05-15",
            "gender": "female",
            "medical_record_number": 100001,
        })
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Alice Testpatient"
        assert body["clinic_id"] == CLINIC_A_ID

    async def test_create_patient_unauthenticated(self, client_anon: httpx.AsyncClient):
        r = await client_anon.post("/api/patients/", json={
            "name": "NoAuth",
        })
        assert r.status_code == 401


class TestListPatients:
    @RLS_XFAIL
    async def test_list_patients_filtered_by_tenant(
        self, client_doctor: httpx.AsyncClient, client_doctor_b: httpx.AsyncClient
    ):
        """Doctor A should only see Clinic A patients; Doctor B only Clinic B."""
        # Create a patient in each clinic
        await client_doctor.post("/api/patients/", json={
            "name": "TenantA Patient",
            "date_of_birth": "2000-01-01",
            "gender": "male",
            "medical_record_number": 200001,
        })
        await client_doctor_b.post("/api/patients/", json={
            "name": "TenantB Patient",
            "date_of_birth": "2000-06-06",
            "gender": "female",
            "medical_record_number": 200002,
        })

        r_a = await client_doctor.get("/api/patients/")
        r_b = await client_doctor_b.get("/api/patients/")
        assert r_a.status_code == 200
        assert r_b.status_code == 200

        names_a = {p["name"] for p in r_a.json()}
        names_b = {p["name"] for p in r_b.json()}
        assert "TenantA Patient" in names_a
        assert "TenantB Patient" not in names_a
        assert "TenantB Patient" in names_b
        assert "TenantA Patient" not in names_b


class TestGetPatient:
    async def test_get_patient_own_clinic(self, client_doctor: httpx.AsyncClient):
        cr = await client_doctor.post("/api/patients/", json={
            "name": "GetMe",
            "date_of_birth": "1985-03-20",
            "gender": "male",
            "medical_record_number": 300001,
        })
        pid = cr.json()["id"]
        r = await client_doctor.get(f"/api/patients/{pid}")
        assert r.status_code == 200
        assert r.json()["name"] == "GetMe"

    @RLS_XFAIL
    async def test_get_patient_cross_tenant_404(
        self, client_doctor: httpx.AsyncClient, client_doctor_b: httpx.AsyncClient
    ):
        """Doctor B must NOT see a patient belonging to Clinic A (RLS)."""
        cr = await client_doctor.post("/api/patients/", json={
            "name": "Hidden",
            "date_of_birth": "1970-01-01",
            "gender": "female",
            "medical_record_number": 300002,
        })
        pid = cr.json()["id"]
        r = await client_doctor_b.get(f"/api/patients/{pid}")
        assert r.status_code == 404


class TestUpdatePatient:
    async def test_update_patient(self, client_doctor: httpx.AsyncClient):
        cr = await client_doctor.post("/api/patients/", json={
            "name": "Updatable",
            "date_of_birth": "1995-12-25",
            "gender": "male",
            "medical_record_number": 400001,
        })
        pid = cr.json()["id"]
        r = await client_doctor.put(f"/api/patients/{pid}", json={
            "name": "Updated Name",
        })
        assert r.status_code == 200
        assert r.json()["name"] == "Updated Name"


class TestDeletePatient:
    async def test_delete_patient(self, client_doctor: httpx.AsyncClient):
        cr = await client_doctor.post("/api/patients/", json={
            "name": "Disposable",
            "date_of_birth": "2002-07-07",
            "gender": "female",
            "medical_record_number": 500001,
        })
        pid = cr.json()["id"]
        r = await client_doctor.delete(f"/api/patients/{pid}")
        assert r.status_code == 204

        r2 = await client_doctor.get(f"/api/patients/{pid}")
        assert r2.status_code == 404
