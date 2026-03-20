from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import Token, UserResponse, UserCreate, TokenData
from app.core.security import create_access_token, get_password_hash, verify_password
from app.api.deps import get_current_user
import uuid

router = APIRouter()

# Mock DB for demonstration
MOCK_USERS_DB = {}

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate):
    if user_in.email in MOCK_USERS_DB:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    user_dict = user_in.dict()
    user_dict["hashed_password"] = get_password_hash(user_in.password)
    del user_dict["password"]
    user_dict["id"] = str(uuid.uuid4())
    
    MOCK_USERS_DB[user_in.email] = user_dict
    return user_dict

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = MOCK_USERS_DB.get(form_data.username) # OAuth2 form uses 'username' field for email
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(
        data={"sub": user["id"], "role": user["role"], "clinic_id": user["clinic_id"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=TokenData)
async def read_users_me(current_user: TokenData = Depends(get_current_user)):
    return current_user
