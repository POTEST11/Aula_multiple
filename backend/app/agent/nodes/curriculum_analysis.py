"""Node 1: Curriculum analysis.

Retrieves and analyzes curriculum standards relevant to the
requested topic, grades, and subject using the MCP tool consultar_estandares.
When a classroom_id is present in the agent state, also queries
class-specific document embeddings via DocumentRetriever.
"""

import logging

from app.agent.state import AgentState
from app.dependencies import async_session_factory
from app.mcp_server.tools import consultar_estandares
from app.rag.document_retriever import DocumentRetriever
from app.rag.embeddings import EmbeddingService
from app.schemas.activity import CurriculumStandard
from app.schemas.document import DocumentChunk

logger = logging.getLogger(__name__)

# Singleton embedding service — the model loads once and is reused across calls.
_embedding_service: EmbeddingService | None = None


def _get_embedding_service() -> EmbeddingService:
    """Lazy-initialize and return the singleton EmbeddingService."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def run(state: AgentState) -> dict:
    """Analyze curriculum standards and retrieve class-specific documents.

    Calls the consultar_estandares MCP tool directly (in-process) to
    retrieve relevant curriculum standards via RAG, then converts them
    into CurriculumStandard model instances. If classroom_id is present,
    also queries class-specific document embeddings.

    Args:
        state: Current agent state with topic, grades, subject, and
            optional classroom_id.

    Returns:
        Partial state update with curriculum_standards, document_context,
        and current_node.
    """
    document_context: list[DocumentChunk] = []

    try:
        results = await consultar_estandares(
            query=state["topic"],
            grades=state["grades"],
            subject=state["subject"],
            top_k=3,
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

    except Exception as exc:
        error_msg = f"curriculum_analysis: {exc}"
        logger.error(error_msg, exc_info=True)
        return {
            "curriculum_standards": [],
            "document_context": [],
            "current_node": "curriculum_analysis",
            "error": error_msg,
        }

    # Class-specific document retrieval (non-fatal)
    classroom_id = state.get("classroom_id")
    if classroom_id:
        try:
            async with async_session_factory() as session:
                retriever = DocumentRetriever(
                    session=session,
                    embedding_service=_get_embedding_service(),
                )
                document_context = await retriever.search(
                    query=state["topic"],
                    classroom_id=classroom_id,
                    top_k=3,
                )
            logger.info(
                "curriculum_analysis: retrieved %d document chunks for classroom_id=%d",
                len(document_context),
                classroom_id,
            )
        except Exception as exc:
            logger.warning(
                "curriculum_analysis: document retrieval failed for classroom_id=%d (non-fatal): %s",
                classroom_id,
                exc,
            )
            document_context = []

    return {
        "curriculum_standards": curriculum_standards,
        "document_context": document_context,
        "current_node": "curriculum_analysis",
    }
