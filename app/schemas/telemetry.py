from pydantic import BaseModel, Field

class TelemetryReadingBase(BaseModel):
    patient_id: str
    heart_rate: float = Field(..., ge=20, le=300)
    spo2: float = Field(..., ge=0, le=100)
    systolic_bp: float = Field(..., ge=40, le=300)
    diastolic_bp: float = Field(..., ge=20, le=200)
    temperature: float = Field(..., ge=30, le=45)

class TelemetryReadingCreate(TelemetryReadingBase):
    pass

class TelemetryReadingResponse(TelemetryReadingBase):
    is_anomaly: bool
    reading_id: str

    class Config:
        from_attributes = True
