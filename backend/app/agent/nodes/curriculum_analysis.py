"""Node 1: Curriculum analysis.

Retrieves and analyzes curriculum standards relevant to the
requested topic, grades, and subject using the MCP tool consultar_estandares.
"""

import logging

from app.agent.state import AgentState
from app.mcp_server.tools import consultar_estandares
from app.schemas.activity import CurriculumStandard

logger = logging.getLogger(__name__)


async def run(state: AgentState) -> dict:
    """Analyze curriculum standards for the given topic and grades.

    Calls the consultar_estandares MCP tool directly (in-process) to
    retrieve relevant curriculum standards via RAG, then converts them
    into CurriculumStandard model instances.

    Args:
        state: Current agent state with topic, grades, and subject.

    Returns:
        Partial state update with curriculum_standards and current_node.
    """
    try:
        results = await consultar_estandares(
            query=state["topic"],
            grades=state["grades"],
            subject=state["subject"],
        )

        curriculum_standards = [
            CurriculumStandard(
                country=item["country"],
                grade=item["grade"],
                subject=item["subject"],
                text=item["text"],
                similarity_score=item.get("score"),
            )
            for item in results
        ]

        logger.info(
            "curriculum_analysis: retrieved %d standards for topic='%s'",
            len(curriculum_standards),
            state["topic"],
        )

        return {
            "curriculum_standards": curriculum_standards,
            "current_node": "curriculum_analysis",
        }

    except Exception as exc:
        error_msg = f"curriculum_analysis: {exc}"
        logger.error(error_msg, exc_info=True)
        return {
            "curriculum_standards": [],
            "current_node": "curriculum_analysis",
            "error": error_msg,
        }
