"""Core configuration."""
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    postgres_user: str
    postgres_password: str
    postgres_db: str
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # RAG / LLM settings (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_chat_model: str = "llama3"
    embedding_dimensions: int = 768
    chunk_size: int = 500
    chunk_overlap: int = 50

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if v in ("", "CHANGE_ME_TO_A_RANDOM_SECRET", "your_secret_key_here"):
            import warnings
            warnings.warn(
                "SECRET_KEY is using a placeholder value. "
                "Set a strong random secret in .env for production.",
                stacklevel=2,
            )
        return v

    class Config:
        env_file = ".env"


settings = Settings()
