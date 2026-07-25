"""Shared test fixtures for integration tests.

Provides an httpx AsyncClient connected to the FastAPI app with
dependency overrides for get_db and get_current_user, enabling
full HTTP-layer integration testing without a real database.

Note: Environment variables must be set BEFORE any app imports so that
pydantic-settings can load Settings at module level.
"""

import os

# Ensure test environment variables are available before any app import
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/testdb")
os.environ.setdefault("LLM_API_KEY", "fake-test-key")
os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("LLM_TIMEOUT_SECONDS", "60")
os.environ.setdefault("EMBEDDING_API_KEY", "fake-test-key")
os.environ.setdefault("JWT_SECRET", "test-secret-for-integration-tests")
os.environ.setdefault("JWT_EXPIRATION_MINUTES", "30")

# Clear the lru_cache so that get_settings() uses our test env vars
from app.config import get_settings  # noqa: E402

get_settings.cache_clear()
