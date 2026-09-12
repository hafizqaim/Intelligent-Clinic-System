import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Integer, Float, Boolean, DateTime, func
from sqlalchemy.orm import mapped_column, Mapped
from app.database import Base
from datetime import datetime




class TelemetryReadings(Base):
    __tablename__ = "telemetry_readings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    heart_rate: Mapped[int] = mapped_column(Integer, nullable=True)
    blood_pressure_systolic: Mapped[int] = mapped_column(Integer, nullable=True)
    blood_pressure_diastolic: Mapped[int] = mapped_column(Integer, nullable=True)
    oxygen_saturation: Mapped[int] = mapped_column(Integer, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, nullable=True)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False)
