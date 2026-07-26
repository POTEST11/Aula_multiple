"""Document retriever using pgvector cosine similarity search for class documents."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_document import ClassDocument
from app.models.document_embedding import DocumentEmbedding
from app.rag.embeddings import EmbeddingService
from app.schemas.document import DocumentChunk


class DocumentRetriever:
    """
    Recupera fragmentos de documentos de clase por similitud semántica usando pgvector.

    Proceso:
    1. Genera embedding local del query (sentence-transformers)
    2. Ejecuta búsqueda cosine similarity en pgvector sobre document_embeddings
    3. Filtra por classroom_id y status="ready" del documento padre
    4. Retorna top_k resultados ordenados por score por encima del umbral
    """

    def __init__(self, session: AsyncSession, embedding_service: EmbeddingService):
        self.session = session
        self.embedding_service = embedding_service

    async def search(
        self,
        query: str,
        classroom_id: int,
        top_k: int = 5,
        similarity_threshold: float = 0.40,
    ) -> list[DocumentChunk]:
        """
        Busca fragmentos de documentos por similitud semántica para un aula específica.

        Args:
            query: Texto de búsqueda (típicamente el tema de la actividad).
            classroom_id: ID del aula cuyos documentos se consultarán.
            top_k: Número máximo de resultados a retornar.
            similarity_threshold: Umbral mínimo de similitud (0-1).

        Returns:
            Lista de DocumentChunk ordenados por similarity_score descendente.
            Lista vacía si ningún resultado supera el umbral.
        """
        # 1. Genera embedding del query
        query_embedding = await self.embedding_service.generate(query)

        # 2. Calcula similarity score: 1 - cosine_distance
        distance = DocumentEmbedding.embedding.cosine_distance(query_embedding)
        similarity_score = (1 - distance).label("similarity_score")

        # 3. Construye query con JOIN a ClassDocument para filtrar status y obtener filename
        stmt = (
            select(
                DocumentEmbedding.content,
                ClassDocument.original_filename,
                similarity_score,
            )
            .join(ClassDocument, DocumentEmbedding.document_id == ClassDocument.id)
            .where(
                DocumentEmbedding.classroom_id == classroom_id,
                ClassDocument.status == "ready",
            )
        )

        # 4. Filtra por umbral, ordena por score desc, limita a top_k
        stmt = (
            stmt.where((1 - distance) >= similarity_threshold)
            .order_by(distance.asc())
            .limit(top_k)
        )

        # 5. Ejecuta y mapea resultados
        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            DocumentChunk(
                content=row.content,
                document_filename=row.original_filename,
                similarity_score=row.similarity_score,
            )
            for row in rows
        ]
