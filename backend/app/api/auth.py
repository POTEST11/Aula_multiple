"""Authentication endpoints: register and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.auth.security import verify_password
from app.crud.users import create_user, get_user_by_email
from app.dependencies import get_current_user, get_db
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account.

    Creates a user with hashed password. Returns 409 if email already exists.
    """
    existing = await get_user_by_email(db, body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado",
        )

    user = await create_user(db, email=body.email, password=body.password, name=body.name)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user and issue a JWT access token.

    Returns 401 if email is not found or password does not match.
    """
    user = await get_user_by_email(db, body.email)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_id=user.id)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user=Depends(get_current_user),
) -> UserResponse:
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)
