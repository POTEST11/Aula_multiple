"""Subject management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.subjects import create_subject, delete_subject, get_subjects_by_user
from app.dependencies import get_current_user, get_db
from app.models.subject import Subject
from app.models.user import User
from app.schemas.subject import SubjectCreate, SubjectResponse

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subject_endpoint(
    body: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubjectResponse:
    """Create a new subject for the authenticated user."""
    subject = await create_subject(db, user_id=current_user.id, name=body.name)
    return SubjectResponse.model_validate(subject)


@router.get("", response_model=list[SubjectResponse])
async def list_subjects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SubjectResponse]:
    """List all subjects belonging to the authenticated user."""
    subjects = await get_subjects_by_user(db, user_id=current_user.id)
    return [SubjectResponse.model_validate(s) for s in subjects]


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject_endpoint(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a subject by ID.

    Verifies that the subject belongs to the current user.
    Sets subject_id=null on associated activities to preserve history.
    """
    result = await db.execute(
        select(Subject).where(Subject.id == subject_id)
    )
    subject = result.scalar_one_or_none()

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Materia no encontrada",
        )

    if subject.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar esta materia",
        )

    await delete_subject(db, subject)
