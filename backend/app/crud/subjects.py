"""CRUD operations for subject management."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.subject import Subject


async def create_subject(db: AsyncSession, user_id: int, name: str) -> Subject:
    """Create a new subject for a user.

    Args:
        db: Async database session.
        user_id: The ID of the owner user.
        name: The subject name.

    Returns:
        The newly created Subject instance.
    """
    subject = Subject(user_id=user_id, name=name)
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return subject


async def get_subjects_by_user(db: AsyncSession, user_id: int) -> list[Subject]:
    """Retrieve all subjects belonging to a user.

    Args:
        db: Async database session.
        user_id: The ID of the owner user.

    Returns:
        List of Subject instances owned by the user.
    """
    result = await db.execute(
        select(Subject).where(Subject.user_id == user_id).order_by(Subject.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_subject(db: AsyncSession, subject: Subject) -> None:
    """Delete a subject and set subject_id=null on associated activities.

    This preserves the activity history by nullifying the foreign key
    rather than cascading the deletion.

    Args:
        db: Async database session.
        subject: The Subject instance to delete.
    """
    await db.execute(
        update(Activity)
        .where(Activity.subject_id == subject.id)
        .values(subject_id=None)
    )
    await db.delete(subject)
    await db.commit()
