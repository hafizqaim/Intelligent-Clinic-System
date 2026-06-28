import os

deps_content = """from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.schemas.auth import TokenData
from app.database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        clinic_id: str = payload.get("clinic_id")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        return TokenData(user_id=user_id, role=role, clinic_id=clinic_id)
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_tenant_db(current_user: TokenData = Depends(get_current_user)) -> AsyncSession:
    async with SessionLocal() as session:
        await session.execute(text(f"SET app.current_tenant = '{current_user.clinic_id}'"))
        yield session
"""

with open('app/api/deps.py', 'w', encoding='utf-8') as f:
    f.write(deps_content)
    
print("Fixed: app/api/deps.py")
