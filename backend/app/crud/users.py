"""CRUD operations for user management."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password
from app.models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Retrieve a user by their email address.

    Args:
        db: Async database session.
        email: The email address to search for.

    Returns:
        The User instance if found, None otherwise.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str, name: str) -> User:
    """Create a new user with a hashed password.

    Args:
        db: Async database session.
        email: The user's email address.
        password: The plaintext password (will be hashed before storage).
        name: The user's display name.

    Returns:
        The newly created User instance.
    """
    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
