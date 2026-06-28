"""Patients router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_current_user, get_tenant_db, require_clinical_staff
from app.schemas.auth import TokenData
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.models.patients import Patients

router = APIRouter()


@router.post("/", response_model=PatientResponse, status_code=201, dependencies=[Depends(require_clinical_staff)])
async def create_patient(
    patient: PatientCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Create a new patient in the current clinic."""
    new_patient = Patients(
        clinic_id=current_user.clinic_id,
        name=patient.name,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender,
        medical_record_number=patient.medical_record_number,
    )
    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)
    return new_patient


@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    skip: int = 0,
    limit: int = 50,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """List patients in the current clinic (RLS-scoped, paginated)."""
    result = await db.execute(select(Patients).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Get a patient by ID (RLS-scoped)."""
    result = await db.execute(select(Patients).where(Patients.id == patient_id))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/{patient_id}", response_model=PatientResponse, dependencies=[Depends(require_clinical_staff)])
async def update_patient(
    patient_id: str,
    updates: PatientUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Update a patient (RLS-scoped)."""
    result = await db.execute(select(Patients).where(Patients.id == patient_id))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)

    await db.commit()
    await db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=204, dependencies=[Depends(require_clinical_staff)])
async def delete_patient(
    patient_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Delete a patient (RLS-scoped)."""
    result = await db.execute(select(Patients).where(Patients.id == patient_id))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    await db.delete(patient)
    await db.commit()
