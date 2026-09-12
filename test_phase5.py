"""Comprehensive Phase 5 end-to-end test."""
import requests
import json
import subprocess
import sys
import traceback

BASE = "http://localhost:8000/api"
TIMEOUT = 10
OUTFILE = open("test_results.txt", "w", encoding="utf-8")

passed = 0
failed = 0

def log(msg):
    print(msg, flush=True)
    OUTFILE.write(msg + "\n")
    OUTFILE.flush()

def check(name, r, expected):
    global passed, failed
    ok = r.status_code == expected
    if ok:
        passed += 1
    else:
        failed += 1
    tag = "PASS" if ok else "FAIL"
    log(f"  [{tag}] {name}: {r.status_code} (expected {expected})")
    try:
        body = r.json()
    except Exception:
        body = r.text[:200]
    if not ok:
        log(f"         Body: {body}")
    return body

def req(method, url, **kwargs):
    kwargs.setdefault("timeout", TIMEOUT)
    log(f"  >> {method.upper()} {url}")
    try:
        return getattr(requests, method)(url, **kwargs)
    except requests.exceptions.Timeout:
        log(f"  !! TIMEOUT after {TIMEOUT}s")
        return None
    except Exception as e:
        log(f"  !! ERROR: {e}")
        return None

try:
    # ═══════════════════════════════════════════════════════════════
    log("\n=== 0. SEED BOOTSTRAP CLINIC ===")
    BOOTSTRAP_CLINIC_ID = "00000000-0000-0000-0000-000000000001"
    seed_sql = (
        f"INSERT INTO clinics (id, name, address, phone_number, created_at) "
        f"VALUES ('{BOOTSTRAP_CLINIC_ID}', 'Bootstrap Clinic', '1 Boot St', '+0000000000', NOW()) "
        f"ON CONFLICT (id) DO NOTHING;"
    )
    result = subprocess.run(
        ["docker", "exec", "intelligent-clinic-system-db-1",
         "psql", "-U", "qaim", "-d", "intelligent_clinic_db", "-c", seed_sql],
        capture_output=True, text=True,
    )
    log(f"  Seed: {result.stdout.strip()} {result.stderr.strip()}")

    # ═══════════════════════════════════════════════════════════════
    log("\n=== 1. AUTH + CLINIC CRUD ===")

    r = req("post", f"{BASE}/auth/register", json={
        "email": "admin@testclinic.com", "password": "StrongPass123!",
        "full_name": "Admin User", "role": "admin", "clinic_id": BOOTSTRAP_CLINIC_ID,
    })
    if r is not None: check("Register admin", r, 201)

    r = req("post", f"{BASE}/auth/login", data={
        "username": "admin@testclinic.com", "password": "StrongPass123!",
    })
    if r is not None:
        login_body = check("Login admin", r, 200)
        token = login_body.get("access_token", "") if isinstance(login_body, dict) else ""
        headers = {"Authorization": f"Bearer {token}"}
    else:
        log("  !! Cannot continue without login")
        raise SystemExit(1)

    r = req("post", f"{BASE}/clinics/", json={
        "name": "Test Clinic", "address": "123 Test Street", "phone_number": "+1234567890",
    }, headers=headers)
    clinic_id = None
    if r is not None:
        clinic_body = check("Create clinic", r, 201)
        clinic_id = clinic_body.get("id") if isinstance(clinic_body, dict) else None
        log(f"         Clinic ID: {clinic_id}")

    r = req("get", f"{BASE}/clinics/", headers=headers)
    if r is not None: check("List clinics", r, 200)

    if clinic_id:
        r = req("get", f"{BASE}/clinics/{clinic_id}", headers=headers)
        if r is not None: check("Get clinic by ID", r, 200)

        r = req("put", f"{BASE}/clinics/{clinic_id}", json={"name": "Updated Clinic Name"}, headers=headers)
        if r is not None:
            upd = check("Update clinic", r, 200)
            if isinstance(upd, dict): log(f"         Updated name: {upd.get('name')}")

    # ═══════════════════════════════════════════════════════════════
    log("\n=== 2. AUTH (Real DB) ===")

    doc_headers = headers  # fallback
    if clinic_id:
        r = req("post", f"{BASE}/auth/register", json={
            "email": "doctor@testclinic.com", "password": "DoctorPass123!",
            "full_name": "Dr. Smith", "role": "doctor", "clinic_id": clinic_id,
        })
        if r is not None: check("Register doctor", r, 201)

        r = req("post", f"{BASE}/auth/login", data={
            "username": "doctor@testclinic.com", "password": "DoctorPass123!",
        })
        if r is not None:
            doc_login = check("Login doctor", r, 200)
            doc_token = doc_login.get("access_token", "") if isinstance(doc_login, dict) else ""
            doc_headers = {"Authorization": f"Bearer {doc_token}"}

        r = req("get", f"{BASE}/auth/me", headers=doc_headers)
        if r is not None:
            me = check("GET /me", r, 200)
            if isinstance(me, dict): log(f"         email={me.get('email')}")

        r = req("post", f"{BASE}/auth/register", json={
            "email": "doctor@testclinic.com", "password": "X",
            "full_name": "Dup", "role": "user", "clinic_id": clinic_id,
        })
        if r is not None: check("Duplicate register (400)", r, 400)

        r = req("post", f"{BASE}/auth/login", data={
            "username": "doctor@testclinic.com", "password": "WrongPassword!",
        })
        if r is not None: check("Wrong password (401)", r, 401)

    # ═══════════════════════════════════════════════════════════════
    log("\n=== 3. PATIENTS CRUD ===")

    patient_id = None
    if clinic_id:
        r = req("post", f"{BASE}/patients/", json={
            "name": "Jane Doe", "date_of_birth": "1990-05-15",
            "gender": "Female", "medical_record_number": 10001,
        }, headers=doc_headers)
        if r is not None:
            pat = check("Create patient", r, 201)
            patient_id = pat.get("id") if isinstance(pat, dict) else None
            log(f"         Patient ID: {patient_id}")

        r = req("get", f"{BASE}/patients/", headers=doc_headers)
        if r is not None:
            lst = check("List patients", r, 200)
            if isinstance(lst, list): log(f"         Count: {len(lst)}")

        if patient_id:
            r = req("get", f"{BASE}/patients/{patient_id}", headers=doc_headers)
            if r is not None: check("Get patient by ID", r, 200)

            r = req("put", f"{BASE}/patients/{patient_id}", json={"name": "Jane Smith"}, headers=doc_headers)
            if r is not None:
                upd = check("Update patient", r, 200)
                if isinstance(upd, dict): log(f"         Updated name: {upd.get('name')}")

    # ═══════════════════════════════════════════════════════════════
    log("\n=== 4. TELEMETRY ===")

    if clinic_id and patient_id:
        r = req("post", f"{BASE}/telemetry/ingest", json={
            "patient_id": patient_id, "clinic_id": clinic_id,
            "heart_rate": 72, "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80, "oxygen_saturation": 98, "temperature": 36.6,
        }, headers=doc_headers)
        if r is not None:
            t = check("Ingest normal", r, 200)
            if isinstance(t, dict): log(f"         is_anomaly: {t.get('is_anomaly')}")

        r = req("post", f"{BASE}/telemetry/ingest", json={
            "patient_id": patient_id, "clinic_id": clinic_id,
            "heart_rate": 200, "blood_pressure_systolic": 250,
            "blood_pressure_diastolic": 160, "oxygen_saturation": 70, "temperature": 41.5,
        }, headers=doc_headers)
        if r is not None:
            t = check("Ingest anomalous", r, 200)
            if isinstance(t, dict): log(f"         is_anomaly: {t.get('is_anomaly')}")

        r = req("get", f"{BASE}/telemetry/readings?patient_id={patient_id}", headers=doc_headers)
        if r is not None:
            rd = check("Get readings", r, 200)
            if isinstance(rd, list): log(f"         Count: {len(rd)}")

        r = req("get", f"{BASE}/telemetry/anomalies?patient_id={patient_id}", headers=doc_headers)
        if r is not None:
            an = check("Get anomalies", r, 200)
            if isinstance(an, list): log(f"         Anomaly count: {len(an)}")

    # ═══════════════════════════════════════════════════════════════
    log("\n=== 5. SECURITY ===")

    r = req("get", f"{BASE}/patients/")
    if r is not None: check("Unauth patients (401)", r, 401)
    r = req("get", f"{BASE}/clinics/")
    if r is not None: check("Unauth clinics (401)", r, 401)
    r = req("post", f"{BASE}/telemetry/ingest", json={})
    if r is not None: check("Unauth telemetry (401)", r, 401)

except Exception as e:
    log(f"\n!!! EXCEPTION: {e}")
    log(traceback.format_exc())

# ═══════════════════════════════════════════════════════════════
log(f"\n{'='*60}")
log(f"RESULTS: {passed} passed, {failed} failed out of {passed+failed}")
log(f"{'='*60}")
OUTFILE.close()
