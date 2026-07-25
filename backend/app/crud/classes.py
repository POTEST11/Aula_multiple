"""CRUD operations for classroom management."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate


async def create_class(
    db: AsyncSession, user_id: int, data: ClassroomCreate
) -> Classroom:
    """Create a new classroom for the given user.

    Args:
        db: Async database session.
        user_id: The ID of the owning user.
        data: Validated classroom creation data.

    Returns:
        The newly created Classroom instance.
    """
    classroom = Classroom(
        user_id=user_id,
        name=data.name,
        grades=data.grades,
    )
    db.add(classroom)
    await db.commit()
    await db.refresh(classroom)
    return classroom


async def get_classes_by_user(db: AsyncSession, user_id: int) -> list[Classroom]:
    """Retrieve all classrooms belonging to a user.

    Args:
        db: Async database session.
        user_id: The ID of the owning user.

    Returns:
        List of Classroom instances ordered by creation date descending.
    """
    result = await db.execute(
        select(Classroom)
        .where(Classroom.user_id == user_id)
        .order_by(Classroom.created_at.desc())
    )
    return list(result.scalars().all())


async def get_class_by_id(
    db: AsyncSession, class_id: int, user_id: int
) -> Classroom | None:
    """Retrieve a single classroom by ID, scoped to the given user.

    Args:
        db: Async database session.
        class_id: The classroom ID.
        user_id: The ID of the owning user.

    Returns:
        The Classroom instance if found and owned by the user, None otherwise.
    """
    result = await db.execute(
        select(Classroom).where(
            Classroom.id == class_id, Classroom.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def update_class(
    db: AsyncSession, classroom: Classroom, data: ClassroomUpdate
) -> Classroom:
    """Update a classroom with the provided fields.

    Args:
        db: Async database session.
        classroom: The existing Classroom instance to update.
        data: Validated update data (only non-None fields are applied).

    Returns:
        The updated Classroom instance.
    """
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(classroom, field, value)
    await db.commit()
    await db.refresh(classroom)
    return classroom


async def delete_class(db: AsyncSession, classroom: Classroom) -> None:
    """Delete a classroom and set classroom_id=null on associated activities.

    This preserves the activity history (denormalized fields like classroom_name
    and grades remain intact) while removing the FK reference.

    Args:
        db: Async database session.
        classroom: The Classroom instance to delete.
    """
    # Nullify classroom_id on associated activities to preserve history
    await db.execute(
        update(Activity)
        .where(Activity.classroom_id == classroom.id)
        .values(classroom_id=None)
    )
    await db.delete(classroom)
    await db.commit()
