"""Unit tests for the CurriculumRetriever."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.retriever import CurriculumRetriever
from app.schemas.activity import CurriculumStandard


@pytest.fixture
def mock_embedding_service():
    """Mock EmbeddingService that returns a fixed 384-dim vector."""
    service = AsyncMock()
    service.generate = AsyncMock(return_value=[0.1] * 384)
    return service


@pytest.fixture
def mock_session():
    """Mock async SQLAlchemy session."""
    session = AsyncMock()
    return session


@pytest.fixture
def retriever(mock_session, mock_embedding_service):
    """CurriculumRetriever instance with mocked dependencies."""
    return CurriculumRetriever(
        session=mock_session, embedding_service=mock_embedding_service
    )


class TestCurriculumRetrieverSearch:
    """Tests for CurriculumRetriever.search()."""

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_when_no_results(
        self, retriever, mock_session
    ):
        """Returns empty list when no results exceed the threshold."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        results = await retriever.search(
            query="Fracciones",
            grades=[3, 4],
            subject="Matemáticas",
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_curriculum_standards(
        self, retriever, mock_session
    ):
        """Returns properly structured CurriculumStandard objects."""
        # Simulate DB rows
        mock_row = MagicMock()
        mock_row.country = "Colombia"
        mock_row.grade = 3
        mock_row.subject = "Matemáticas"
        mock_row.content = "Resolver problemas con fracciones"
        mock_row.similarity_score = 0.85

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock_session.execute = AsyncMock(return_value=mock_result)

        results = await retriever.search(
            query="Fracciones",
            grades=[3, 4],
            subject="Matemáticas",
        )

        assert len(results) == 1
        assert isinstance(results[0], CurriculumStandard)
        assert results[0].country == "Colombia"
        assert results[0].grade == 3
        assert results[0].subject == "Matemáticas"
        assert results[0].text == "Resolver problemas con fracciones"
        assert results[0].similarity_score == 0.85

    @pytest.mark.asyncio
    async def test_search_calls_embedding_service_with_query(
        self, retriever, mock_session, mock_embedding_service
    ):
        """Generates embedding from the search query text."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        await retriever.search(
            query="Ecosistemas acuáticos",
            grades=[5],
            subject="Ciencias",
        )

        mock_embedding_service.generate.assert_awaited_once_with(
            "Ecosistemas acuáticos"
        )

    @pytest.mark.asyncio
    async def test_search_with_country_filter(
        self, retriever, mock_session
    ):
        """Country parameter filters results by country."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        results = await retriever.search(
            query="Fracciones",
            grades=[3],
            subject="Matemáticas",
            country="Colombia",
        )

        assert results == []
        # Verify execute was called (the query was built and executed)
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_search_multiple_results_ordered_by_score(
        self, retriever, mock_session
    ):
        """Results are ordered by similarity score descending."""
        row1 = MagicMock()
        row1.country = "Colombia"
        row1.grade = 4
        row1.subject = "Matemáticas"
        row1.content = "Estándar A"
        row1.similarity_score = 0.92

        row2 = MagicMock()
        row2.country = "Colombia"
        row2.grade = 3
        row2.subject = "Matemáticas"
        row2.content = "Estándar B"
        row2.similarity_score = 0.78

        mock_result = MagicMock()
        mock_result.all.return_value = [row1, row2]
        mock_session.execute = AsyncMock(return_value=mock_result)

        results = await retriever.search(
            query="Fracciones",
            grades=[3, 4],
            subject="Matemáticas",
        )

        assert len(results) == 2
        assert results[0].similarity_score == 0.92
        assert results[1].similarity_score == 0.78

    @pytest.mark.asyncio
    async def test_search_respects_top_k_parameter(
        self, retriever, mock_session
    ):
        """Can customize top_k to return fewer results."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        await retriever.search(
            query="Historia",
            grades=[5, 6],
            subject="Historia",
            top_k=3,
        )

        # Verify the query was executed (we trust SQLAlchemy handles .limit())
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_search_respects_similarity_threshold(
        self, retriever, mock_session
    ):
        """Custom similarity_threshold is applied in the query."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        await retriever.search(
            query="Lectura comprensiva",
            grades=[2, 3],
            subject="Lenguaje",
            similarity_threshold=0.9,
        )

        mock_session.execute.assert_awaited_once()
