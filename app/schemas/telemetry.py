from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class TelemetryReadingCreate(BaseModel):
    patient_id: UUID
    clinic_id: UUID
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    oxygen_saturation: Optional[int] = None
    temperature: Optional[float] = None

    class Config:
        from_attributes = True


class TelemetryReadingResponse(BaseModel):
    id: UUID
    patient_id: UUID
    clinic_id: UUID
    timestamp: datetime
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    oxygen_saturation: Optional[int] = None
    temperature: Optional[float] = None
    is_anomaly: bool

    class Config:
        from_attributes = True
