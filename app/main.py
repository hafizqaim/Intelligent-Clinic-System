from fastapi import FastAPI
from app.api.routers import auth, telemetry, rag, clinics, patients

app = FastAPI(
    title="Intelligent Clinic System API",
    version="1.0.0",
    description="Backend API for telemetry monitoring, anomaly detection, and clinical RAG."
)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
app.include_router(rag.router, prefix="/rag", tags=["RAG"])
app.include_router(clinics.router, prefix="/clinics", tags=["Clinics"])
app.include_router(patients.router, prefix="/patients", tags=["Patients"])