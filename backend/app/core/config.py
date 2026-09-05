from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    GROQ_API_KEY: str
    LLM_MODEL: str = 'qwen/qwen3.8-27b'
    EMBEDDING_MODEL: str = 'all-MiniLM-L6-v2'
    MAX_UPLOAD_SIZE_MB: int = 50
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    CORS_ORIGINS: str = 'http://localhost:5173,http://localhost:3000'
    RATE_LIMIT_PER_MINUTE: int = 30
    UPLOAD_DIR: str = './uploads'
    CHROMA_PERSIST_DIR: str = './chroma_data'
    DATABASE_URL: str = 'sqlite+aiosqlite:///./researchlens.db'

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
