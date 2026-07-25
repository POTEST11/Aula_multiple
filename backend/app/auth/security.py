"""Password hashing utilities using bcrypt via passlib."""

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt hash string.
    """
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain: The plaintext password to verify.
        hashed: The bcrypt hash to compare against.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    return _pwd_context.verify(plain, hashed)
