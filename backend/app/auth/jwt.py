"""JWT token creation and verification."""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import get_settings

ALGORITHM = "HS256"


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token containing the user_id.

    Args:
        user_id: The ID of the authenticated user.
        expires_delta: Optional custom expiration duration.
            Defaults to Settings.JWT_EXPIRATION_MINUTES.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token.

    Args:
        token: The encoded JWT string.

    Returns:
        The decoded payload dictionary.

    Raises:
        HTTPException: 401 if the token is invalid or expired.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: falta identificador de usuario",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
