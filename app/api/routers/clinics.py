"""Clinics router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_current_user, get_tenant_db, require_admin
from app.schemas.auth import TokenData
from app.schemas.clinic import ClinicCreate, ClinicUpdate, ClinicResponse
from app.models.clinic import Clinics
from app.database import SessionLocal

router = APIRouter()


async def _get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()


@router.post("/", response_model=ClinicResponse, status_code=201, dependencies=[Depends(require_admin)])
async def create_clinic(
    clinic: ClinicCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(_get_db),
):
    """Create a new clinic."""
    new_clinic = Clinics(
        name=clinic.name,
        address=clinic.address,
        phone_number=clinic.phone_number,
    )
    db.add(new_clinic)
    await db.commit()
    await db.refresh(new_clinic)
    return new_clinic


@router.get("/", response_model=List[ClinicResponse])
async def list_clinics(
    skip: int = 0,
    limit: int = 50,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(_get_db),
):
    """List all clinics (paginated)."""
    result = await db.execute(select(Clinics).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/me", response_model=ClinicResponse)
async def get_my_clinic(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(_get_db),
):
    """Get the current user's clinic."""
    result = await db.execute(select(Clinics).where(Clinics.id == current_user.clinic_id))
    clinic = result.scalars().first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic


@router.get("/{clinic_id}", response_model=ClinicResponse)
async def get_clinic(
    clinic_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(_get_db),
):
    """Get clinic by ID."""
    result = await db.execute(select(Clinics).where(Clinics.id == clinic_id))
    clinic = result.scalars().first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic


@router.put("/{clinic_id}", response_model=ClinicResponse, dependencies=[Depends(require_admin)])
async def update_clinic(
    clinic_id: str,
    updates: ClinicUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(_get_db),
):
    """Update a clinic."""
    result = await db.execute(select(Clinics).where(Clinics.id == clinic_id))
    clinic = result.scalars().first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(clinic, field, value)

    await db.commit()
    await db.refresh(clinic)
    return clinic


@router.delete("/{clinic_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_clinic(
    clinic_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(_get_db),
):
    """Delete a clinic."""
    result = await db.execute(select(Clinics).where(Clinics.id == clinic_id))
    clinic = result.scalars().first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    await db.delete(clinic)
    await db.commit()
