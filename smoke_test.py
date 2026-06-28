"""
End-to-end smoke test for the Intelligent Clinic System.
Exercises: health check, auth, clinics, patients, telemetry (ingest + anomaly detection).

Usage:  python smoke_test.py           (server must be running on localhost:8000)
"""
import httpx
import sys
import uuid
import psycopg2

BASE = "http://localhost:8000"
DB_URL = "postgresql://qaim:qaim123@localhost:5432/intelligent_clinic_db"
PASS = 0
FAIL = 0


def step(label: str):
    print(f"\n{'='*60}\n  {label}\n{'='*60}")


def check(name: str, resp: httpx.Response, expected_status: int = 200):
    global PASS, FAIL
    ok = resp.status_code == expected_status
    symbol = "[PASS]" if ok else "[FAIL]"
    print(f"  {symbol} {name} -> {resp.status_code}")
    if not ok:
        print(f"         Expected {expected_status}, body: {resp.text[:300]}")
        FAIL += 1
    else:
        PASS += 1
    return ok


def seed_clinic() -> str:
    """Insert a bootstrap clinic directly via SQL (avoids auth chicken-and-egg)."""
    clinic_id = str(uuid.uuid4())
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO clinics (id, name, address, phone_number, created_at) "
        "VALUES (%s, %s, %s, %s, NOW()) ON CONFLICT DO NOTHING",
        (clinic_id, "SmokeTest Clinic", "123 Test St", "555-0100"),
    )
    cur.close()
    conn.close()
    return clinic_id


def main():
    global PASS, FAIL
    c = httpx.Client(base_url=BASE, timeout=15)

    # ── 1. Health check ──────────────────────────────────────────
    step("1. Health Check")
    r = c.get("/health")
    check("GET /health", r)
    if r.status_code == 200:
        data = r.json()
        print(f"         database : {data.get('database')}")
        print(f"         ml_model : {data.get('ml_model')}")
        print(f"         ollama   : {data.get('ollama')}")

    # ── 2. Seed a clinic (direct DB — bootstrap for auth) ──────
    step("2. Seed Clinic (bootstrap)")
    clinic_id = seed_clinic()
    print(f"  [PASS] Clinic seeded via SQL")
    print(f"         clinic_id: {clinic_id}")
    PASS += 1

    # ── 3. Register an admin user ────────────────────────────────
    step("3. Register Admin User")
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@test.com"
    admin_payload = {
        "email": admin_email,
        "password": "Admin123!",
        "full_name": "Smoke Admin",
        "role": "admin",
        "clinic_id": clinic_id,
    }
    r = c.post("/api/auth/register", json=admin_payload)
    check("POST /api/auth/register (admin)", r, 201)

    # ── 4. Login ─────────────────────────────────────────────────
    step("4. Login")
    r = c.post("/api/auth/login", data={"username": admin_email, "password": "Admin123!"})
    check("POST /api/auth/login", r)
    if r.status_code == 200:
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"         token: {token[:30]}...")
    else:
        print("  [SKIP] Cannot proceed without token.")
        sys.exit(1)

    # ── 5. Get current user info ─────────────────────────────────
    step("5. Get Current User (/me)")
    r = c.get("/api/auth/me", headers=headers)
    check("GET /api/auth/me", r)

    # ── 6. Register a doctor user ────────────────────────────────
    step("6. Register Doctor User")
    doctor_email = f"doctor_{uuid.uuid4().hex[:6]}@test.com"
    doctor_payload = {
        "email": doctor_email,
        "password": "Doctor123!",
        "full_name": "Smoke Doctor",
        "role": "doctor",
        "clinic_id": clinic_id,
    }
    r = c.post("/api/auth/register", json=doctor_payload)
    check("POST /api/auth/register (doctor)", r, 201)

    # Login as doctor
    r = c.post("/api/auth/login", data={"username": doctor_email, "password": "Doctor123!"})
    check("POST /api/auth/login (doctor)", r)
    doctor_token = r.json()["access_token"]
    doctor_headers = {"Authorization": f"Bearer {doctor_token}"}

    # ── 7. Create a patient ──────────────────────────────────────
    step("7. Create Patient")
    patient_payload = {
        "name": "Jane Smoke",
        "date_of_birth": "1990-05-15",
        "gender": "female",
        "medical_record_number": 100001,
    }
    r = c.post("/api/patients/", json=patient_payload, headers=doctor_headers)
    check("POST /api/patients/", r, 201)
    if r.status_code == 201:
        patient = r.json()
        patient_id = patient["id"]
        print(f"         patient_id: {patient_id}")
    else:
        print(f"         body: {r.text[:200]}")
        patient_id = None

    # ── 8. List patients ─────────────────────────────────────────
    step("8. List Patients")
    r = c.get("/api/patients/", headers=doctor_headers)
    check("GET /api/patients/", r)
    if r.status_code == 200:
        patients = r.json()
        print(f"         count: {len(patients)}")

    # ── 9. Ingest NORMAL telemetry ───────────────────────────────
    step("9. Ingest Normal Telemetry")
    if patient_id:
        normal_reading = {
            "patient_id": patient_id,
            "clinic_id": clinic_id,
            "heart_rate": 72,
            "blood_pressure_systolic": 118,
            "blood_pressure_diastolic": 76,
            "oxygen_saturation": 98,
            "temperature": 36.8,
        }
        r = c.post("/api/telemetry/ingest", json=normal_reading, headers=doctor_headers)
        check("POST /api/telemetry/ingest (normal)", r, 200)
        if r.status_code == 201:
            data = r.json()
            print(f"         is_anomaly: {data.get('is_anomaly')}")

    # ── 10. Ingest ANOMALOUS telemetry ───────────────────────────
    step("10. Ingest Anomalous Telemetry")
    if patient_id:
        anomalous_reading = {
            "patient_id": patient_id,
            "clinic_id": clinic_id,
            "heart_rate": 185,
            "blood_pressure_systolic": 210,
            "blood_pressure_diastolic": 130,
            "oxygen_saturation": 82,
            "temperature": 40.8,
        }
        r = c.post("/api/telemetry/ingest", json=anomalous_reading, headers=doctor_headers)
        check("POST /api/telemetry/ingest (anomalous)", r, 200)
        if r.status_code == 201:
            data = r.json()
            print(f"         is_anomaly: {data.get('is_anomaly')}")
            if not data.get("is_anomaly"):
                print("         [WARN] Expected anomaly=True for extreme vitals!")

    # ── 11. Get telemetry readings ───────────────────────────────
    step("11. Query Telemetry Readings")
    r = c.get("/api/telemetry/readings", params={"patient_id": patient_id}, headers=doctor_headers)
    check("GET /api/telemetry/readings", r)
    if r.status_code == 200:
        readings = r.json()
        print(f"         count: {len(readings)}")

    # ── 12. Get anomalies ────────────────────────────────────────
    step("12. Query Anomalies")
    r = c.get("/api/telemetry/anomalies", params={"patient_id": patient_id}, headers=doctor_headers)
    check("GET /api/telemetry/anomalies", r)
    if r.status_code == 200:
        anomalies = r.json()
        print(f"         anomaly_count: {len(anomalies)}")

    # ── 13. List clinics ─────────────────────────────────────────
    step("13. List Clinics")
    r = c.get("/api/clinics/", headers=headers)
    check("GET /api/clinics/", r)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  SMOKE TEST COMPLETE: {PASS} passed, {FAIL} failed")
    print(f"{'='*60}")

    c.close()
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
