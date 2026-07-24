"""Application settings using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str

    # LLM
    LLM_API_KEY: str
    LLM_PROVIDER: str
    LLM_TIMEOUT_SECONDS: int = 60

    # Embeddings
    EMBEDDING_API_KEY: str

    # JWT
    JWT_SECRET: str
    JWT_EXPIRATION_MINUTES: int


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings (singleton)."""
    return Settings()
