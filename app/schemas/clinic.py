"""Clinic schemas."""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ClinicCreate(BaseModel):
    name: str
    address: str
    phone_number: str


class ClinicUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None


class ClinicResponse(BaseModel):
    id: UUID
    name: str
    address: str
    phone_number: str
    created_at: datetime

    class Config:
        from_attributes = True
