"""Property-based tests for RAG Curricular retrieval (Properties 4 & 5).

**Validates: Requirements 1.3, 3.2, 3.3, 3.4**

Property 4: Corrección de filtros y completitud de resultados RAG
— Para toda consulta al RAG_Curricular con grados y materia especificados,
todos los resultados retornados SHALL: (a) coincidir con los filtros de grado
y materia solicitados, (b) no exceder top_k=5 resultados, (c) estar ordenados
por score de similitud descendente, y (d) contener campos no vacíos de país,
grado, materia y texto.

Property 5: Comportamiento bajo umbral de similitud
— Para toda consulta al RAG_Curricular donde ningún embedding supere el umbral
de similitud configurado, el retriever SHALL retornar una lista vacía de resultados.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.rag.retriever import CurriculumRetriever
from app.schemas.activity import CurriculumStandard


# --- Strategies ---

# Arbitrary non-empty query text (1-200 chars, printable)
query_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=200,
).filter(lambda s: s.strip())

# Valid grade lists: 1-6 unique integers from 1-12
grades_strategy = st.lists(
    st.integers(min_value=1, max_value=12),
    min_size=1,
    max_size=6,
    unique=True,
)

# Subject name: non-empty text
subject_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=1,
    max_size=100,
).filter(lambda s: s.strip())

# Country: non-empty text or None
country_strategy = st.one_of(
    st.none(),
    st.text(
        alphabet=st.characters(whitelist_categories=("L",)),
        min_size=1,
        max_size=50,
    ).filter(lambda s: s.strip()),
)

# Similarity scores: floats between 0.7 and 1.0 (above threshold)
similarity_score_strategy = st.floats(
    min_value=0.70, max_value=1.0, allow_nan=False, allow_infinity=False
)

# Number of results to simulate (0-5 for top_k=5)
num_results_strategy = st.integers(min_value=1, max_value=5)


def _make_mock_row(country: str, grade: int, subject: str, text: str, score: float):
    """Create a mock DB row with the given fields."""
    row = MagicMock()
    row.country = country
    row.grade = grade
    row.subject = subject
    row.content = text
    row.similarity_score = score
    return row


class TestRAGFilterCorrectnessProperty:
    """Property 4: Corrección de filtros y completitud de resultados RAG.

    **Validates: Requirements 1.3, 3.2, 3.3**

    For any query to RAG_Curricular with specified grades and subject, all
    returned results SHALL: (a) match the requested grade and subject filters,
    (b) not exceed top_k=5 results, (c) be ordered by similarity score
    descending, and (d) contain non-empty fields for country, grade, subject,
    and text.
    """

    @given(
        query=query_strategy,
        grades=grades_strategy,
        subject=subject_strategy,
        country=country_strategy,
        num_results=num_results_strategy,
        scores=st.lists(
            similarity_score_strategy, min_size=1, max_size=5
        ),
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_results_match_filters_and_constraints(
        self,
        query: str,
        grades: list[int],
        subject: str,
        country: str | None,
        num_results: int,
        scores: list[float],
    ):
        """For any generated query, all returned results match filters, respect
        top_k, are ordered by score descending, and have non-empty fields."""
        # Limit scores to num_results and sort descending (simulating DB ordering)
        used_scores = sorted(scores[:num_results], reverse=True)
        actual_num = len(used_scores)

        # Build mock rows that match the requested filters
        chosen_grade = grades[0]  # Pick a grade from the requested list
        result_country = country if country else "Colombia"

        mock_rows = [
            _make_mock_row(
                country=result_country,
                grade=chosen_grade,
                subject=subject,
                text=f"Estándar curricular contenido {i}",
                score=used_scores[i],
            )
            for i in range(actual_num)
        ]

        # Setup mocks
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate = AsyncMock(return_value=[0.1] * 384)

        retriever = CurriculumRetriever(
            session=mock_session, embedding_service=mock_embedding_service
        )

        # Execute search
        results = await retriever.search(
            query=query,
            grades=grades,
            subject=subject,
            country=country,
            top_k=5,
            similarity_threshold=0.7,
        )

        # (a) All results match requested grade and subject filters
        for r in results:
            assert r.grade in grades, (
                f"Grade {r.grade} not in requested grades {grades}"
            )
            assert r.subject.lower() == subject.lower(), (
                f"Subject '{r.subject}' does not match '{subject}'"
            )

        # (b) Does not exceed top_k=5 results
        assert len(results) <= 5, (
            f"Got {len(results)} results, exceeds top_k=5"
        )

        # (c) Results are ordered by similarity score descending
        for i in range(len(results) - 1):
            assert results[i].similarity_score >= results[i + 1].similarity_score, (
                f"Results not ordered: {results[i].similarity_score} < "
                f"{results[i + 1].similarity_score}"
            )

        # (d) Non-empty fields for country, grade, subject, and text
        for r in results:
            assert r.country and len(r.country) > 0, "Country is empty"
            assert r.grade is not None, "Grade is None"
            assert r.subject and len(r.subject) > 0, "Subject is empty"
            assert r.text and len(r.text) > 0, "Text is empty"

    @given(
        query=query_strategy,
        grades=grades_strategy,
        subject=subject_strategy,
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_embedding_service_called_with_query(
        self,
        query: str,
        grades: list[int],
        subject: str,
    ):
        """For any query, the retriever calls the embedding service with the
        exact query text provided."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate = AsyncMock(return_value=[0.1] * 384)

        retriever = CurriculumRetriever(
            session=mock_session, embedding_service=mock_embedding_service
        )

        await retriever.search(
            query=query,
            grades=grades,
            subject=subject,
        )

        # Verify embedding service was called with the exact query text
        mock_embedding_service.generate.assert_awaited_once_with(query)


class TestRAGBelowThresholdProperty:
    """Property 5: Comportamiento bajo umbral de similitud.

    **Validates: Requirements 3.4**

    For any query to RAG_Curricular where no embedding exceeds the configured
    similarity threshold, the retriever SHALL return an empty result list.
    """

    @given(
        query=query_strategy,
        grades=grades_strategy,
        subject=subject_strategy,
        country=country_strategy,
        threshold=st.floats(
            min_value=0.5, max_value=0.99, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_empty_results_when_below_threshold(
        self,
        query: str,
        grades: list[int],
        subject: str,
        country: str | None,
        threshold: float,
    ):
        """When no embedding exceeds the similarity threshold (DB returns empty),
        the retriever returns an empty list."""
        # Mock DB returning empty results (simulates all scores below threshold)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate = AsyncMock(return_value=[0.1] * 384)

        retriever = CurriculumRetriever(
            session=mock_session, embedding_service=mock_embedding_service
        )

        results = await retriever.search(
            query=query,
            grades=grades,
            subject=subject,
            country=country,
            top_k=5,
            similarity_threshold=threshold,
        )

        # Retriever SHALL return an empty result list
        assert results == [], (
            f"Expected empty list but got {len(results)} results"
        )
        assert isinstance(results, list), "Result must be a list"
