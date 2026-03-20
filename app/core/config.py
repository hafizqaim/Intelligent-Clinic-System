from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Intelligent Clinic API"
    secret_key: str = "super_secret_key_change_me_in_prod"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        extra = "ignore" # Ignore unseen fields from .env

settings = Settings()
