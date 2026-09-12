# Intelligent Clinic System

A multi-tenant backend for clinic operations — patient records, live vitals telemetry with
ML-based anomaly detection, and a document-grounded RAG assistant — built on FastAPI,
async SQLAlchemy, and PostgreSQL with Row-Level Security.

A lightweight built-in web console (`/ui`) is included for exercising every endpoint without
needing a separate frontend or an API client.

---

## 1. Project overview

Each clinic using the system is a **tenant**. Multiple clinics share one deployment and one
database, but a clinic can never see another clinic's data — that isolation is enforced by
PostgreSQL itself (Row-Level Security), not just by application code.

Core capabilities:

- **Auth & RBAC** — JWT-based login, with roles (`admin`, `doctor`, `nurse`, `user`) gating
  who can create clinics, patients, and telemetry.
- **Patients & Clinics** — standard CRUD, scoped per tenant.
- **Telemetry & anomaly detection** — every vitals reading (heart rate, blood pressure, O2
  saturation, temperature) is scored on ingestion by an Isolation Forest model and flagged
  as normal or anomalous in real time.
- **RAG assistant** — upload a clinical document (PDF/TXT/MD), it's chunked and embedded
  into pgvector, and clinicians can ask questions answered *only* from their clinic's own
  uploaded documents, with sources cited.
- **Web console** — a single-page UI at `/ui` for logging in and using every feature above
  by hand: dashboard, patients, telemetry, and the RAG chat.

---

## 2. Architecture

```
┌──────────────┐        JWT (role + clinic_id)        ┌────────────────────────┐
│  /ui console │ ───────────────────────────────────▶ │   FastAPI application  │
│ (static SPA) │ ◀─────────────────────────────────── │       (app/main.py)    │
└──────────────┘              JSON over HTTP           └───────────┬────────────┘
                                                                    │
                        ┌───────────────────────────────────────────┼───────────────────────┐
                        │                                           │                       │
                 ┌──────▼───────┐                          ┌────────▼────────┐    ┌─────────▼─────────┐
                 │  Auth & RBAC │                          │   Telemetry     │    │   RAG pipeline     │
                 │ (JWT, roles) │                          │  + ML anomaly   │    │  (chunk → embed →  │
                 └──────┬───────┘                          │   detection     │    │   retrieve → chat) │
                        │                                  └────────┬────────┘    └─────────┬─────────┘
                        │                                           │                       │
                        │                                  ┌────────▼────────┐    ┌─────────▼─────────┐
                        │                                  │ Isolation Forest│    │   Gemini API       │
                        │                                  │  (scikit-learn, │    │ (embeddings + chat,│
                        │                                  │  loaded once at │    │  free tier)        │
                        │                                  │  app startup)   │    └─────────┬─────────┘
                        │                                  └─────────────────┘              │
                        └──────────────────────┬────────────────────────────────────────────┘
                                                │
                                       ┌────────▼─────────┐
                                       │   PostgreSQL      │
                                       │  + pgvector       │
                                       │  + Row-Level      │
                                       │    Security        │
                                       └────────────────────┘
```

**How a request is scoped to one tenant:** every JWT carries `clinic_id` alongside the
user's role. Most endpoints depend on `get_tenant_db` (`app/api/deps.py`), which opens a
database session and runs `SELECT set_config('app.current_tenant', :clinic_id, false)`
before the request handler ever touches the database. A per-table RLS policy
(`clinic_id = current_setting('app.current_tenant', true)::uuid`, see the
`enable_rls` migration) then transparently filters every query — a handler can't
accidentally leak another clinic's rows even if it forgets to add a `WHERE` clause.

**How telemetry gets scored:** an Isolation Forest model (`app/ml/predictor.py`), trained
offline (`ml_models/train_model.py`) and loaded once into memory at startup via FastAPI's
`lifespan` hook, scores each incoming reading synchronously on ingest — no batch job, no
queue, the anomaly flag comes back in the same response.

**How the RAG assistant answers:** a document is split into overlapping text chunks
(`app/services/rag_service.py`), all chunks are embedded in a single batched call to
Gemini's `text-embedding-004`, and the vectors are stored in a `pgvector` column scoped
by `clinic_id`. A question is embedded the same way, the nearest chunks are retrieved
with a cosine-distance query, and Gemini's `gemini-2.0-flash` is asked to answer using
*only* that retrieved context — it's explicitly instructed to say so if the context isn't
enough, rather than guess.

### Tech stack

| Layer | Choice |
|---|---|
| API framework | FastAPI + Uvicorn (async throughout) |
| Database | PostgreSQL 16 + `pgvector` |
| ORM / migrations | SQLAlchemy 2.0 (async) + Alembic |
| Auth | JWT (`python-jose`) + bcrypt password hashing |
| ML | scikit-learn (Isolation Forest) |
| RAG / LLM | Google Gemini API (embeddings + chat), free tier |
| Frontend | Static single-page console served by FastAPI itself (`app/static/index.html`) |
| Logging | `structlog`, JSON or console output |
| Containerization | Docker + Docker Compose |
| CI | GitHub Actions (`.github/workflows/ci.yml`) |

---

## 3. Project structure

```
Intelligent-Clinic-System/
├── app/
│   ├── main.py                  # FastAPI app factory, lifespan (ML model load), /health
│   ├── database.py              # Async engine/session factory
│   ├── api/
│   │   ├── deps.py              # get_current_user, get_tenant_db (RLS scoping), RBAC
│   │   └── routers/
│   │       ├── auth.py          # register / login / me
│   │       ├── clinics.py       # clinic CRUD (admin-gated)
│   │       ├── patients.py      # patient CRUD (RLS-scoped)
│   │       ├── telemetry.py     # ingest + anomaly/reading queries
│   │       └── rag.py           # document upload, query, chat history
│   ├── core/
│   │   ├── config.py            # pydantic-settings, reads .env
│   │   ├── security.py          # JWT + bcrypt helpers
│   │   ├── middleware.py        # CORS, request-ID tracing, error handling
│   │   └── logging.py           # structlog setup
│   ├── ml/
│   │   └── predictor.py         # Isolation Forest anomaly detector
│   ├── services/
│   │   └── rag_service.py       # chunking, Gemini embeddings/chat, retrieval
│   ├── models/                  # SQLAlchemy ORM models (one per table)
│   ├── schemas/                 # Pydantic request/response schemas
│   └── static/
│       └── index.html           # the /ui web console (vanilla HTML/CSS/JS, no build step)
├── alembic/
│   └── versions/                # init schema → enable RLS → pgvector/RAG fixes → embedding dim
├── ml_models/
│   ├── train_model.py           # offline training script
│   ├── synthetic_vitals.csv     # training data
│   └── telemetry_anomaly_model.pkl
├── tests/                       # pytest integration suite (real Postgres, real HTTP client)
├── smoke_test.py                # end-to-end smoke test against a running server
├── docker-compose.yml           # postgres + app
├── Dockerfile
├── requirements.txt / requirements-dev.txt
└── .env.example
```

---

## 4. Running it

### Prerequisites

- Docker + Docker Compose (recommended path), **or** Python 3.12 + a local PostgreSQL 16
  with the `pgvector` extension available
- A free Gemini API key from **https://aistudio.google.com/apikey** (only needed for the
  RAG upload/query endpoints — everything else works without it)

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env
# edit .env: set POSTGRES_USER/PASSWORD, a real SECRET_KEY, and GEMINI_API_KEY

docker compose up -d --build
```

This starts Postgres (with `pgvector`) and the API on `http://localhost:8000`. Then apply
migrations once the database is up:

```bash
docker compose exec app alembic upgrade head
```

### Option B — Run locally against a Dockerized database

```bash
docker compose up -d db
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Using it

- **API docs (Swagger UI):** http://localhost:8000/docs
- **Web console:** http://localhost:8000/ui/ — register/login, then create clinics,
  patients, log telemetry readings, and use the RAG assistant, all from the browser
- **Health check:** http://localhost:8000/health — reports database, ML model, and Gemini
  configuration status

There's no public "create a tenant" endpoint by design — registering a user requires an
existing `clinic_id`. Bootstrap your first clinic either by inserting one directly in
Postgres, or by registering the first `admin` user against a manually-created clinic row,
then creating further clinics through the API/console from there.

### Running the tests

```bash
pytest
```

The suite runs against a real PostgreSQL instance (see `tests/conftest.py`) — start
`docker compose up -d db` first. A handful of RLS-isolation tests are skipped if your
database user is a Postgres superuser, since RLS policies don't apply to superusers.

### Environment variables

See `.env.example` for the full list. The ones you must set yourself:

| Variable | Purpose |
|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Database credentials |
| `DATABASE_URL` | Full async connection string |
| `SECRET_KEY` | JWT signing secret — must not be left at the placeholder value |
| `GEMINI_API_KEY` | Required for document upload and RAG chat |
