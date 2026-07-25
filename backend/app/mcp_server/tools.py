"""MCP tools for curriculum standards retrieval."""

from app.dependencies import async_session_factory
from app.mcp_server.server import mcp
from app.rag.embeddings import EmbeddingService
from app.rag.retriever import CurriculumRetriever

# Singleton embedding service — the model loads once and is reused across calls.
_embedding_service: EmbeddingService | None = None


def _get_embedding_service() -> EmbeddingService:
    """Lazy-initialize and return the singleton EmbeddingService."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


@mcp.tool()
async def consultar_estandares(
    query: str,
    grades: list[int],
    subject: str,
    country: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Recupera estándares curriculares relevantes mediante búsqueda semántica.

    Args:
        query: Texto de búsqueda (típicamente el tema de la actividad)
        grades: Lista de grados escolares a consultar
        subject: Materia/asignatura
        country: País (opcional, filtra por país específico)
        top_k: Número máximo de resultados a retornar

    Returns:
        Lista de estándares con: country, grade, subject, text, score
    """
    embedding_service = _get_embedding_service()

    async with async_session_factory() as session:
        retriever = CurriculumRetriever(
            session=session,
            embedding_service=embedding_service,
        )
        results = await retriever.search(
            query=query,
            grades=grades,
            subject=subject,
            country=country,
            top_k=top_k,
        )

    return [
        {
            "country": std.country,
            "grade": std.grade,
            "subject": std.subject,
            "text": std.text,
            "score": std.similarity_score,
        }
        for std in results
    ]
