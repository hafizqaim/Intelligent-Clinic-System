"""Telemetry router with ML-based anomaly detection."""

from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime

from app.schemas.telemetry import TelemetryReadingCreate, TelemetryReadingResponse
from app.api.deps import get_current_user, get_tenant_db
from app.ml.predictor import detector
from app.schemas.auth import TokenData

router = APIRouter()


@router.post("/ingest", response_model=TelemetryReadingResponse)
async def ingest_telemetry(
    reading: TelemetryReadingCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Ingest patient telemetry, detect anomalies with ML, and persist to database."""
    vital_signs = [
        reading.heart_rate,
        reading.blood_pressure_systolic,
        reading.blood_pressure_diastolic,
        reading.oxygen_saturation,
        reading.temperature,
    ]

    is_anomaly = bool(detector.predict(vital_signs))
    reading_id = str(uuid.uuid4())
    now = datetime.utcnow()

    await db.execute(
        text(
            """
            INSERT INTO telemetry_readings
                (id, clinic_id, patient_id, timestamp, heart_rate,
                 blood_pressure_systolic, blood_pressure_diastolic,
                 oxygen_saturation, temperature, is_anomaly)
            VALUES
                (CAST(:id AS uuid), CAST(:clinic_id AS uuid), CAST(:patient_id AS uuid),
                 :ts, :hr, :bp_sys, :bp_dia, :o2, :temp, :anomaly)
            """
        ),
        {
            "id": reading_id,
            "clinic_id": str(reading.clinic_id),
            "patient_id": str(reading.patient_id),
            "ts": now,
            "hr": reading.heart_rate,
            "bp_sys": reading.blood_pressure_systolic,
            "bp_dia": reading.blood_pressure_diastolic,
            "o2": reading.oxygen_saturation,
            "temp": reading.temperature,
            "anomaly": is_anomaly,
        },
    )
    await db.commit()

    return TelemetryReadingResponse(
        id=reading_id,
        patient_id=reading.patient_id,
        clinic_id=reading.clinic_id,
        timestamp=now,
        heart_rate=reading.heart_rate,
        blood_pressure_systolic=reading.blood_pressure_systolic,
        blood_pressure_diastolic=reading.blood_pressure_diastolic,
        oxygen_saturation=reading.oxygen_saturation,
        temperature=reading.temperature,
        is_anomaly=is_anomaly,
    )


@router.get("/anomalies", response_model=List[TelemetryReadingResponse])
async def get_patient_anomalies(
    patient_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Get anomalous readings for a patient (RLS-scoped)."""
    result = await db.execute(
        text(
            """
            SELECT id, clinic_id, patient_id, timestamp, heart_rate,
                   blood_pressure_systolic, blood_pressure_diastolic,
                   oxygen_saturation, temperature, is_anomaly
            FROM telemetry_readings
            WHERE patient_id = CAST(:pid AS uuid) AND is_anomaly = true
            ORDER BY timestamp DESC
            """
        ),
        {"pid": patient_id},
    )
    rows = result.fetchall()
    return [
        TelemetryReadingResponse(
            id=r.id,
            clinic_id=r.clinic_id,
            patient_id=r.patient_id,
            timestamp=r.timestamp,
            heart_rate=r.heart_rate,
            blood_pressure_systolic=r.blood_pressure_systolic,
            blood_pressure_diastolic=r.blood_pressure_diastolic,
            oxygen_saturation=r.oxygen_saturation,
            temperature=r.temperature,
            is_anomaly=r.is_anomaly,
        )
        for r in rows
    ]


@router.get("/readings", response_model=List[TelemetryReadingResponse])
async def get_patient_readings(
    patient_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Get all readings for a patient (RLS-scoped)."""
    result = await db.execute(
        text(
            """
            SELECT id, clinic_id, patient_id, timestamp, heart_rate,
                   blood_pressure_systolic, blood_pressure_diastolic,
                   oxygen_saturation, temperature, is_anomaly
            FROM telemetry_readings
            WHERE patient_id = CAST(:pid AS uuid)
            ORDER BY timestamp DESC
            """
        ),
        {"pid": patient_id},
    )
    rows = result.fetchall()
    return [
        TelemetryReadingResponse(
            id=r.id,
            clinic_id=r.clinic_id,
            patient_id=r.patient_id,
            timestamp=r.timestamp,
            heart_rate=r.heart_rate,
            blood_pressure_systolic=r.blood_pressure_systolic,
            blood_pressure_diastolic=r.blood_pressure_diastolic,
            oxygen_saturation=r.oxygen_saturation,
            temperature=r.temperature,
            is_anomaly=r.is_anomaly,
        )
        for r in rows
    ]
    #     select(TelemetryReadings).where(
    #         TelemetryReadings.patient_id == patient_id,
    #         TelemetryReadings.is_anomaly == True,
    #     )
    # )
    return []
