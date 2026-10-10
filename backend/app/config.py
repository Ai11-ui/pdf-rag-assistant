from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PDF RAG Assistant API"
    frontend_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_upload_size_mb: int = 15
    default_top_k: int = 4
    max_top_k: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
