"""Curriculum standards retriever using pgvector cosine similarity search."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curriculum_embedding import CurriculumEmbedding
from app.rag.embeddings import EmbeddingService
from app.schemas.activity import CurriculumStandard


class CurriculumRetriever:
    """
    Recupera estándares curriculares por similitud semántica usando pgvector.

    Proceso:
    1. Genera embedding local del query (sentence-transformers)
    2. Ejecuta búsqueda cosine similarity en pgvector
    3. Filtra por grado, materia y umbral de similitud
    4. Retorna top_k resultados ordenados por score
    """

    def __init__(self, session: AsyncSession, embedding_service: EmbeddingService):
        self.session = session
        self.embedding_service = embedding_service

    async def search(
        self,
        query: str,
        grades: list[int],
        subject: str,
        country: str | None = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> list[CurriculumStandard]:
        """
        Busca estándares curriculares por similitud semántica.

        Args:
            query: Texto de búsqueda (típicamente el tema de la actividad).
            grades: Lista de grados escolares a consultar.
            subject: Materia/asignatura (búsqueda case-insensitive).
            country: País (opcional, filtra por país específico).
            top_k: Número máximo de resultados a retornar.
            similarity_threshold: Umbral mínimo de similitud (0-1).

        Returns:
            Lista de CurriculumStandard ordenados por score descendente.
            Lista vacía si ningún resultado supera el umbral.
        """
        # 1. Genera embedding del query
        query_embedding = await self.embedding_service.generate(query)

        # 2. Calcula similarity score: 1 - cosine_distance
        distance = CurriculumEmbedding.embedding.cosine_distance(query_embedding)
        similarity_score = (1 - distance).label("similarity_score")

        # 3. Construye query con filtros
        stmt = select(
            CurriculumEmbedding.country,
            CurriculumEmbedding.grade,
            CurriculumEmbedding.subject,
            CurriculumEmbedding.content,
            similarity_score,
        ).where(
            CurriculumEmbedding.grade.in_(grades),
            func.lower(CurriculumEmbedding.subject) == func.lower(subject),
        )

        # Filtro opcional por país
        if country is not None:
            stmt = stmt.where(
                func.lower(CurriculumEmbedding.country) == func.lower(country)
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
            CurriculumStandard(
                country=row.country,
                grade=row.grade,
                subject=row.subject,
                text=row.content,
                similarity_score=row.similarity_score,
            )
            for row in rows
        ]
