from pydantic_settings import BaseSettings

class Settings(BaseSettings):
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

        class Config:
            env_file = ".env"

settings = Settings()
