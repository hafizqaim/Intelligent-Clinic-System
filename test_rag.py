"""End-to-end test for Phase 4 RAG pipeline."""
import requests, json

BASE = "http://localhost:8000/api"

# 1. Register a user
print("=== 1. Register ===")
r = requests.post(f"{BASE}/auth/register", json={
    "email": "ragtest2@clinic.com",
    "password": "testpass123",
    "full_name": "RAG Tester",
    "role": "doctor",
    "clinic_id": "00000000-0000-0000-0000-000000000001",
})
print(f"  Status: {r.status_code}")
print(f"  Body: {r.json()}")

# 2. Login
print("\n=== 2. Login ===")
r = requests.post(f"{BASE}/auth/login", data={
    "username": "ragtest2@clinic.com",
    "password": "testpass123",
})
print(f"  Status: {r.status_code}")
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"  Token: {token[:30]}...")

# 3. Upload a text document
print("\n=== 3. Upload Document ===")
doc_content = """
Patient Care Guidelines for Intelligent Clinic System

Chapter 1: Vital Signs Monitoring
Heart rate should be monitored continuously for ICU patients.
Normal resting heart rate for adults is between 60 and 100 beats per minute.
Blood pressure should be checked at least every 4 hours for inpatients.
Normal blood pressure is around 120/80 mmHg.

Chapter 2: Emergency Protocols
If a patient's oxygen saturation drops below 90%, immediate intervention is required.
Administer supplemental oxygen and notify the attending physician.
For cardiac emergencies, follow the ACLS protocol.

Chapter 3: Medication Management
All medications must be verified against the patient's allergy list.
Double-check dosages for pediatric patients.
Controlled substances require dual verification before administration.
"""

r = requests.post(
    f"{BASE}/rag/upload",
    headers=headers,
    files={"file": ("guidelines.txt", doc_content.encode(), "text/plain")},
)
print(f"  Status: {r.status_code}")
try:
    body = r.json()
    print(f"  Body: {body}")
except Exception:
    print(f"  Text: {r.text[:500]}")

if r.status_code == 500:
    print("  NOTE: 500 likely means OPENAI_API_KEY is not set. Set it in .env to enable embedding generation.")

# 4. Query the documents
print("\n=== 4. RAG Query ===")
r = requests.post(
    f"{BASE}/rag/query",
    headers=headers,
    json={"query": "What is the normal heart rate for adults?", "top_k": 3},
)
print(f"  Status: {r.status_code}")
try:
    body = r.json()
    print(f"  Answer: {body.get('answer', body)}")
    print(f"  Sources: {body.get('sources', [])}")
except Exception:
    print(f"  Text: {r.text[:500]}")

if r.status_code == 500:
    print("  NOTE: 500 likely means OPENAI_API_KEY is not set.")

# 5. Get chat history
print("\n=== 5. Chat History ===")
r = requests.get(f"{BASE}/rag/history", headers=headers)
print(f"  Status: {r.status_code}")
try:
    print(f"  Messages: {json.dumps(r.json(), indent=2, default=str)}")
except Exception:
    print(f"  Text: {r.text[:500]}")

# 6. Test unsupported file type
print("\n=== 6. Upload unsupported file type ===")
r = requests.post(
    f"{BASE}/rag/upload",
    headers=headers,
    files={"file": ("data.csv", b"a,b,c\n1,2,3", "text/csv")},
)
print(f"  Status: {r.status_code}")
try:
    print(f"  Body: {r.json()}")
except Exception:
    print(f"  Text: {r.text[:500]}")

# 7. Test unauthenticated access
print("\n=== 7. Unauthenticated access ===")
r = requests.post(f"{BASE}/rag/upload")
print(f"  Status: {r.status_code} (expected 401)")

print("\n=== ALL TESTS DONE ===")
