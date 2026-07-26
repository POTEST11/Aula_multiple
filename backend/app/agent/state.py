"""Agent state definition for the activity generation graph."""

from typing import Optional, TypedDict

from app.schemas.activity import ActivityOutput, CurriculumStandard
from app.schemas.document import DocumentChunk


class AgentState(TypedDict):
    """State passed through the LangGraph activity generation pipeline.

    Contains input fields, intermediate outputs from each node,
    and control fields for tracking execution.
    """

    # Entrada
    topic: str
    grades: list[int]
    subject: str
    available_resources: list[str]
    classroom_id: Optional[int]

    # Nodo 1 output - Análisis curricular
    curriculum_standards: list[CurriculumStandard]
    document_context: list[DocumentChunk]

    # Nodo 2 output - Diseño de actividad
    anchor_activity_draft: Optional[str]
    variants_draft: Optional[dict[int, str]]

    # Nodo 3 output - Adaptación de recursos
    anchor_activity_adapted: Optional[str]
    variants_adapted: Optional[dict[int, str]]

    # Nodo 4 output - Formateo de salida
    final_output: Optional[ActivityOutput]

    # Control
    current_node: str
    error: Optional[str]
