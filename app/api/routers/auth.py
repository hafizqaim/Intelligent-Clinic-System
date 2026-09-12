"""Authentication router."""
from fastapi import APIRouter, HTTPException, Depends
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.schemas.auth import TokenData, Token, UserCreate, UserResponse
from app.api.deps import get_current_user
from app.database import SessionLocal
from app.models.users import Users

router = APIRouter()


async def _get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user: UserCreate, db: AsyncSession = Depends(_get_db)):
    """Register a new user."""
    result = await db.execute(select(Users).where(Users.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = Users(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        role=user.role,
        clinic_id=user.clinic_id,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role.value if hasattr(new_user.role, 'value') else new_user.role,
        clinic_id=new_user.clinic_id,
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(_get_db)):
    """Login and get JWT token."""
    result = await db.execute(select(Users).where(Users.email == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value if hasattr(user.role, 'value') else user.role,
            "clinic_id": str(user.clinic_id),
        },
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(_get_db),
):
    """Get current user info."""
    result = await db.execute(select(Users).where(Users.id == current_user.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, 'value') else user.role,
        clinic_id=user.clinic_id,
    )
