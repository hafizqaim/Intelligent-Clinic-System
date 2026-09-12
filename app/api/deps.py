from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.schemas.auth import TokenData
from app.database import SessionLocal
from sqlalchemy import text
from typing import Sequence

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        clinic_id: str = payload.get("clinic_id")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return TokenData(user_id=user_id, role=role, clinic_id=clinic_id)

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_tenant_db(current_user: TokenData = Depends(get_current_user)):
    session = SessionLocal()
    try:
        # Set RLS context variable using parameterized query
        await session.execute(
            text("SELECT set_config('app.current_tenant', :tenant_id, false)"),
            {"tenant_id": current_user.clinic_id},
        )
        yield session
    finally:
        # Not resetting app.current_tenant here on purpose: set_config(..., false)
        # is session-scoped, so this connection can return to the pool still
        # carrying it and be reused by an unrelated request (e.g. a plain
        # login/register session). That's handled where it actually matters --
        # the RLS policy itself guards against a stale/empty value via NULLIF
        # (see the guard_rls_policy_cast migration) -- rather than here, since
        # any extra query in this teardown runs after the response is already
        # computed, and an error here would incorrectly turn an already-
        # successful request into a 500.
        await session.close()


class RoleChecker:
    """Dependency that enforces role-based access control.

    Usage::

        admin_only = RoleChecker(["admin"])

        @router.post("/", dependencies=[Depends(admin_only)])
        async def create_clinic(...):
            ...
    """

    def __init__(self, allowed_roles: Sequence[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(
        self, current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user


# Pre-built role checkers for convenience
require_admin = RoleChecker(["admin"])
require_admin_or_doctor = RoleChecker(["admin", "doctor"])
require_clinical_staff = RoleChecker(["admin", "doctor", "nurse"])
