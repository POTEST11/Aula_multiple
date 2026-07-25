"""CRUD operations for activity history persistence."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.activity import Activity, ActivityVariant, VariantStandard
from app.schemas.activity import ActivityOutput


async def save_activity(
    db: AsyncSession,
    *,
    user_id: int,
    output: ActivityOutput,
    classroom_id: int | None = None,
    subject_id: int | None = None,
) -> Activity:
    """Persist a generated activity with its variants and standards.

    Creates the Activity record plus all nested ActivityVariant and
    VariantStandard rows in a single transaction.

    Args:
        db: Async database session.
        user_id: The ID of the authenticated user.
        output: The validated ActivityOutput from the agent graph.
        classroom_id: Optional FK to a classroom.
        subject_id: Optional FK to a subject.

    Returns:
        The persisted Activity instance with relationships loaded.
    """
    activity = Activity(
        user_id=user_id,
        classroom_id=classroom_id,
        subject_id=subject_id,
        topic=output.topic,
        grades=output.grades,
        subject_name=output.subject_name,
        classroom_name=output.classroom_name,
        available_resources=output.available_resources,
        anchor_activity=output.anchor_activity,
    )
    db.add(activity)
    await db.flush()  # Get activity.id without committing

    for variant in output.variants:
        db_variant = ActivityVariant(
            activity_id=activity.id,
            grade=variant.grade,
            content=variant.content,
            instructions=variant.instructions,
            exercises=variant.exercises,
        )
        db.add(db_variant)
        await db.flush()  # Get db_variant.id for standards

        for standard in variant.aligned_standards:
            db_standard = VariantStandard(
                variant_id=db_variant.id,
                curriculum_embedding_id=None,
                standard_text=standard.text,
                country=standard.country,
                grade=standard.grade,
                subject=standard.subject,
            )
            db.add(db_standard)

    await db.commit()
    await db.refresh(activity)
    return activity


async def list_history(
    db: AsyncSession,
    *,
    user_id: int,
    subject_id: int | None = None,
    class_id: int | None = None,
    search: str | None = None,
) -> list[Activity]:
    """List activities for a user with optional filters, ordered by date desc.

    Args:
        db: Async database session.
        user_id: The ID of the authenticated user.
        subject_id: Optional filter by subject.
        class_id: Optional filter by classroom.
        search: Optional keyword to search in topic or anchor_activity.

    Returns:
        List of Activity instances matching the filters.
    """
    stmt = (
        select(Activity)
        .where(Activity.user_id == user_id)
        .order_by(Activity.created_at.desc())
    )

    if subject_id is not None:
        stmt = stmt.where(Activity.subject_id == subject_id)

    if class_id is not None:
        stmt = stmt.where(Activity.classroom_id == class_id)

    if search:
        keyword = f"%{search}%"
        stmt = stmt.where(
            or_(
                Activity.topic.ilike(keyword),
                Activity.anchor_activity.ilike(keyword),
            )
        )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_activity_by_id(
    db: AsyncSession,
    *,
    activity_id: int,
    user_id: int,
) -> Activity | None:
    """Get a full activity with variants and standards by ID.

    Args:
        db: Async database session.
        activity_id: The activity primary key.
        user_id: The ID of the authenticated user (ownership check).

    Returns:
        The Activity with relationships loaded, or None if not found.
    """
    stmt = (
        select(Activity)
        .where(Activity.id == activity_id, Activity.user_id == user_id)
        .options(
            selectinload(Activity.variants).selectinload(ActivityVariant.standards)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_activity(
    db: AsyncSession,
    *,
    activity: Activity,
) -> None:
    """Permanently delete an activity and its related variants/standards.

    Args:
        db: Async database session.
        activity: The Activity instance to delete.
    """
    await db.delete(activity)
    await db.commit()
