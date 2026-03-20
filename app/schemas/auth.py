from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str | None = None
    role: str | None = None
    clinic_id: str | None = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    clinic_id: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    clinic_id: str

    class Config:
        from_attributes = True
