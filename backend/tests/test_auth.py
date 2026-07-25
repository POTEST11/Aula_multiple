"""Unit tests for the authentication module (security + JWT)."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.auth.jwt import create_access_token, verify_token
from app.auth.security import hash_password, verify_password


# --- Password hashing tests ---


class TestPasswordHashing:
    """Tests for hash_password and verify_password."""

    def test_hash_password_returns_bcrypt_hash(self):
        hashed = hash_password("mi_contraseña_segura")
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_verify_password_correct(self):
        password = "contraseña123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("contraseña_correcta")
        assert verify_password("contraseña_incorrecta", hashed) is False

    def test_hash_password_different_each_time(self):
        """bcrypt uses a random salt, so two hashes of the same password differ."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2

    def test_verify_password_empty_string(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False


# --- JWT tests ---


_FAKE_SETTINGS = {
    "JWT_SECRET": "test-secret-key-for-unit-tests",
    "JWT_EXPIRATION_MINUTES": 30,
    "DATABASE_URL": "postgresql+asyncpg://x:x@localhost/test",
    "LLM_API_KEY": "fake",
    "LLM_PROVIDER": "groq",
    "EMBEDDING_API_KEY": "fake",
}


def _mock_settings():
    """Create a mock settings object with test values."""
    from app.config import Settings

    return Settings(**_FAKE_SETTINGS)


class TestJWT:
    """Tests for create_access_token and verify_token."""

    @patch("app.auth.jwt.get_settings", return_value=_mock_settings())
    def test_create_and_verify_token(self, mock_settings):
        token = create_access_token(user_id=42)
        payload = verify_token(token)
        assert payload["sub"] == "42"
        assert "exp" in payload

    @patch("app.auth.jwt.get_settings", return_value=_mock_settings())
    def test_create_token_custom_expiration(self, mock_settings):
        token = create_access_token(user_id=7, expires_delta=timedelta(minutes=5))
        payload = verify_token(token)
        assert payload["sub"] == "7"

    @patch("app.auth.jwt.get_settings", return_value=_mock_settings())
    def test_verify_invalid_token_raises_401(self, mock_settings):
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here")
        assert exc_info.value.status_code == 401

    @patch("app.auth.jwt.get_settings", return_value=_mock_settings())
    def test_verify_expired_token_raises_401(self, mock_settings):
        token = create_access_token(
            user_id=1, expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401

    @patch("app.auth.jwt.get_settings", return_value=_mock_settings())
    def test_verify_token_without_sub_raises_401(self, mock_settings):
        """A token without 'sub' claim should be rejected."""
        from jose import jwt as jose_jwt

        settings = _mock_settings()
        bad_token = jose_jwt.encode(
            {"exp": 9999999999}, settings.JWT_SECRET, algorithm="HS256"
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_token(bad_token)
        assert exc_info.value.status_code == 401
