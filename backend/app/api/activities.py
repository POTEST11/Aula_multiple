"""Activity generation endpoint."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import build_activity_graph
from app.config import get_settings
from app.crud.history import save_activity
from app.dependencies import get_current_user, get_db
from app.models.classroom import Classroom
from app.models.subject import Subject
from app.models.user import User
from app.schemas.activity import ActivityOutput, GenerateRequest

router = APIRouter(prefix="/activities", tags=["activities"])

settings = get_settings()


@router.post("/generate", response_model=ActivityOutput)
async def generate_activity(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ActivityOutput:
    """Generate a pedagogical activity with grade-specific variants.

    Invokes the LangGraph agent pipeline with a global timeout.
    Persists the result in the activity history before returning.

    Args:
        request: Validated generation request (topic, grades 2-6, subject, etc.).
        current_user: The authenticated teacher.
        db: Async database session.

    Returns:
        The complete ActivityOutput including the persisted database ID.

    Raises:
        HTTPException 404: If the specified classroom or subject is not found.
        HTTPException 500: If the agent graph returns an error.
        HTTPException 504: If the LLM service does not respond within the timeout.
    """
    classroom_name: str | None = None
    subject_name: str = request.subject_name

    # Look up classroom name for denormalization
    if request.classroom_id is not None:
        result = await db.execute(
            select(Classroom).where(
                Classroom.id == request.classroom_id,
                Classroom.user_id == current_user.id,
            )
        )
        classroom = result.scalar_one_or_none()
        if classroom is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clase no encontrada",
            )
        classroom_name = classroom.name

    # Look up subject name for denormalization (override if subject_id provided)
    if request.subject_id is not None:
        result = await db.execute(
            select(Subject).where(
                Subject.id == request.subject_id,
                Subject.user_id == current_user.id,
            )
        )
        subject = result.scalar_one_or_none()
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Materia no encontrada",
            )
        subject_name = subject.name

    # Build initial state for the agent graph
    initial_state = {
        "topic": request.topic,
        "grades": request.grades,
        "subject": subject_name,
        "available_resources": request.available_resources or [],
        "classroom_id": request.classroom_id,
        "curriculum_standards": [],
        "document_context": [],
        "anchor_activity_draft": None,
        "variants_draft": None,
        "anchor_activity_adapted": None,
        "variants_adapted": None,
        "final_output": None,
        "current_node": "",
        "error": None,
    }

    # Invoke the LangGraph pipeline with a global timeout
    graph = build_activity_graph()
    try:
        result_state = await asyncio.wait_for(
            graph.ainvoke(initial_state),
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="El servicio de IA no respondió en el tiempo esperado. Por favor, intente nuevamente.",
        )

    # Check for agent-level errors
    if result_state.get("error"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la generación de actividad: {result_state['error']}",
        )

    # Extract the final output
    output: ActivityOutput | None = result_state.get("final_output")
    if output is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El agente no produjo una salida válida.",
        )

    # Enrich output with denormalized fields before persisting
    output.classroom_name = classroom_name
    output.subject_name = subject_name

    # Persist the activity in history
    activity = await save_activity(
        db,
        user_id=current_user.id,
        output=output,
        classroom_id=request.classroom_id,
        subject_id=request.subject_id,
    )

    # Enrich output with persisted fields
    output.id = activity.id
    output.created_at = activity.created_at.isoformat()

    return output
