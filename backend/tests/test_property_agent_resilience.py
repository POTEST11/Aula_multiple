"""Property-based test for agent resilience (Property 13).

**Validates: Requirement 7.2**

Property 13: Agent Resilience — For any execution of the Curriculum_Analysis_Node
where document retrieval raises an exception, the node still returns valid
curriculum_standards results and an empty document_context list.
"""

import os

# Set required environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("EMBEDDING_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_EXPIRATION_MINUTES", "60")

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.agent.nodes import curriculum_analysis
from app.schemas.activity import CurriculumStandard


# --- Strategies ---

# Valid topic: non-empty string of 3-100 characters
topic_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=3,
    max_size=100,
).filter(lambda t: len(t.strip()) >= 3)

# Valid grades: 2-6 unique integers from 1-12
grades_strategy = st.lists(
    st.integers(min_value=1, max_value=12),
    min_size=2,
    max_size=6,
    unique=True,
)

# Valid subject
subject_strategy = st.sampled_from([
    "Matemáticas", "Lenguaje", "Ciencias Naturales", "Ciencias Sociales",
    "Arte", "Educación Física", "Tecnología", "Inglés",
])

# Valid classroom_id (always present to trigger document retrieval path)
classroom_id_strategy = st.integers(min_value=1, max_value=10000)

# Exception types that could be raised during document retrieval
exception_strategy = st.sampled_from([
    RuntimeError("Connection pool exhausted"),
    ConnectionError("Database connection refused"),
    TimeoutError("Query timed out"),
    OSError("Network unreachable"),
    ValueError("Invalid embedding dimension"),
    Exception("Unexpected internal error"),
])


# --- Helpers ---

def _make_mock_curriculum_results(grades: list[int], subject: str) -> list[dict]:
    """Create mock results from consultar_estandares."""
    return [
        {
            "country": "CO",
            "grade": g,
            "subject": subject,
            "text": f"Estándar curricular para grado {g}",
            "score": 0.85,
        }
        for g in grades
    ]


class TestPropertyAgentResilience:
    """Property 13: Agent Resilience.

    **Validates: Requirement 7.2**

    For any execution of the Curriculum_Analysis_Node where document retrieval
    raises an exception, the node still returns valid curriculum_standards
    results and an empty document_context list.
    """

    @given(
        topic=topic_strategy,
        grades=grades_strategy,
        subject=subject_strategy,
        classroom_id=classroom_id_strategy,
        exc=exception_strategy,
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_node_returns_valid_results_when_document_retrieval_fails(
        self,
        topic: str,
        grades: list[int],
        subject: str,
        classroom_id: int,
        exc: Exception,
    ):
        """The curriculum_analysis node returns valid curriculum_standards and
        empty document_context when DocumentRetriever.search raises any exception."""

        # Build the agent state with classroom_id present
        state = {
            "topic": topic,
            "grades": sorted(grades),
            "subject": subject,
            "available_resources": [],
            "classroom_id": classroom_id,
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

        # Mock consultar_estandares to return valid curriculum results
        mock_curriculum_results = _make_mock_curriculum_results(grades, subject)

        # Mock async_session_factory context manager to raise the exception
        # when DocumentRetriever.search is called
        mock_session = AsyncMock()
        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock(return_value=False)

        mock_factory = MagicMock(return_value=mock_session_cm)

        # Mock DocumentRetriever.search to raise the exception
        mock_retriever_instance = AsyncMock()
        mock_retriever_instance.search = AsyncMock(side_effect=exc)

        with (
            patch(
                "app.agent.nodes.curriculum_analysis.consultar_estandares",
                new_callable=AsyncMock,
                return_value=mock_curriculum_results,
            ) as mock_consultar,
            patch(
                "app.agent.nodes.curriculum_analysis.async_session_factory",
                mock_factory,
            ),
            patch(
                "app.agent.nodes.curriculum_analysis.DocumentRetriever",
                return_value=mock_retriever_instance,
            ),
            patch(
                "app.agent.nodes.curriculum_analysis._get_embedding_service",
                return_value=MagicMock(),
            ),
        ):
            result = await curriculum_analysis.run(state)

        # Verify curriculum_standards are valid and non-empty
        assert "curriculum_standards" in result
        assert len(result["curriculum_standards"]) > 0
        assert len(result["curriculum_standards"]) == len(grades)

        # Verify each standard is a valid CurriculumStandard
        for std in result["curriculum_standards"]:
            assert isinstance(std, CurriculumStandard)
            assert std.country == "CO"
            assert std.subject == subject
            assert std.grade in grades

        # Verify document_context is an empty list (resilience behavior)
        assert "document_context" in result
        assert result["document_context"] == []

        # Verify current_node is set correctly
        assert result["current_node"] == "curriculum_analysis"

        # Verify no error is propagated (document failure is non-fatal)
        assert result.get("error") is None
