"""Classroom CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.classes import (
    create_class as crud_create_class,
    delete_class as crud_delete_class,
    get_class_by_id,
    get_classes_by_user,
    update_class as crud_update_class,
)
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.classroom import ClassroomCreate, ClassroomResponse, ClassroomUpdate

router = APIRouter(prefix="/classes", tags=["classes"])


@router.post(
    "/",
    response_model=ClassroomResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_class(
    data: ClassroomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClassroomResponse:
    """Create a new classroom for the authenticated user.

    Validates that the class has between 2 and 6 grades (enforced by schema).
    """
    classroom = await crud_create_class(db, user_id=current_user.id, data=data)
    return ClassroomResponse.model_validate(classroom)


@router.get("/", response_model=list[ClassroomResponse])
async def list_classes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ClassroomResponse]:
    """List all classrooms belonging to the authenticated user."""
    classrooms = await get_classes_by_user(db, user_id=current_user.id)
    return [ClassroomResponse.model_validate(c) for c in classrooms]


@router.put("/{class_id}", response_model=ClassroomResponse)
async def update_class(
    class_id: int,
    data: ClassroomUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClassroomResponse:
    """Update a classroom. Only the owner can modify their classroom."""
    classroom = await get_class_by_id(db, class_id=class_id, user_id=current_user.id)
    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada",
        )
    updated = await crud_update_class(db, classroom=classroom, data=data)
    return ClassroomResponse.model_validate(updated)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a classroom. Associated activities are preserved with classroom_id set to null.

    Denormalized fields (classroom_name, grades) on activities remain intact.
    """
    classroom = await get_class_by_id(db, class_id=class_id, user_id=current_user.id)
    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada",
        )
    await crud_delete_class(db, classroom=classroom)
