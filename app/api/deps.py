from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.schemas.auth import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        clinic_id: str = payload.get("clinic_id")
        
        if user_id is None:
            raise credentials_exception
            
        return TokenData(user_id=user_id, role=role, clinic_id=clinic_id)
        
    except JWTError:
        raise credentials_exception

async def get_tenant_db(current_user: TokenData = Depends(get_current_user)):
    """
    Mock DB dependency setting Row Level Security (RLS)
    In reality you'd open AsyncSession and execute:
        await db.execute(text(f"SET app.current_clinic_id = '{current_user.clinic_id}'"))
    """
    db_session = {"clinic_id_rls": current_user.clinic_id, "user_id": current_user.user_id}
    return db_session
