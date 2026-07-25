"""History endpoints: list, detail, and delete activities."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.history import delete_activity, get_activity_by_id, list_history
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.activity import ActivityOutput, CurriculumStandard, VariantOutput
from app.schemas.history import HistorySummary

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistorySummary])
async def get_history(
    subject_id: int | None = None,
    class_id: int | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[HistorySummary]:
    """List activity history for the authenticated user.

    Supports optional filters by subject, class, and keyword search.
    Results are ordered by creation date descending.
    """
    activities = await list_history(
        db,
        user_id=current_user.id,
        subject_id=subject_id,
        class_id=class_id,
        search=search,
    )
    return [HistorySummary.model_validate(a) for a in activities]


@router.get("/{activity_id}", response_model=ActivityOutput)
async def get_activity_detail(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivityOutput:
    """Get full activity detail including variants and aligned standards."""
    activity = await get_activity_by_id(
        db, activity_id=activity_id, user_id=current_user.id
    )
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad no encontrada",
        )

    # Build the response from ORM model
    variants = [
        VariantOutput(
            grade=v.grade,
            content=v.content,
            instructions=v.instructions,
            exercises=v.exercises,
            aligned_standards=[
                CurriculumStandard(
                    country=s.country,
                    grade=s.grade,
                    subject=s.subject,
                    text=s.standard_text,
                )
                for s in v.standards
            ],
        )
        for v in activity.variants
    ]

    return ActivityOutput(
        id=activity.id,
        topic=activity.topic,
        grades=activity.grades,
        subject_name=activity.subject_name,
        classroom_name=activity.classroom_name,
        available_resources=activity.available_resources or [],
        anchor_activity=activity.anchor_activity,
        variants=variants,
        created_at=activity.created_at.isoformat(),
    )


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity_endpoint(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Permanently delete an activity by ID.

    Verifies that the activity belongs to the authenticated user.
    """
    activity = await get_activity_by_id(
        db, activity_id=activity_id, user_id=current_user.id
    )
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad no encontrada",
        )

    await delete_activity(db, activity=activity)
