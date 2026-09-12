"""Patient schemas."""

from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class PatientCreate(BaseModel):
    name: str
    date_of_birth: str
    gender: str
    medical_record_number: int


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    medical_record_number: Optional[int] = None


class PatientResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    name: str
    date_of_birth: str
    gender: str
    medical_record_number: int

    class Config:
        from_attributes = True
