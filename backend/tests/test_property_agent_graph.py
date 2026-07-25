"""Property-based tests for the LangGraph agent graph (Properties 1, 2, 3, 6).

**Validates: Requirements 1.1, 2.1, 2.5, 2.6, 1.4**

Property 1: Invariante estructural de salida - For any valid generation request
with N grades (2 ≤ N ≤ 6), a non-empty topic, and a subject, the agent output
SHALL contain exactly one anchor activity and exactly N variants, and the
complete output SHALL validate against the ActivityOutput Pydantic schema.

Property 2: Orden secuencial de ejecución de nodos - The graph SHALL execute
nodes in order: curriculum_analysis → activity_design → resource_adaptation →
output_formatting.

Property 3: Identificación de nodo en errores - If a node fails, the error
message SHALL identify which node failed (error starts with node name).

Property 6: Alineación variante-estándar - Each variant's aligned_standards
SHALL only contain standards whose grade matches that variant's grade.
"""

import json
import os
from unittest.mock import AsyncMock, patch

# Set required environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("EMBEDDING_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_EXPIRATION_MINUTES", "60")

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.agent.graph import build_activity_graph
from app.agent.nodes import output_formatting
from app.schemas.activity import ActivityOutput, CurriculumStandard, VariantOutput


# --- Strategies ---

# Valid topic: non-empty string of 3-100 characters
topic_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=3,
    max_size=100,
).filter(lambda t: len(t.strip()) >= 3)

# Valid grades: 2-6 unique integers from 1-12
grades_strategy = st.integers(min_value=2, max_value=6).flatmap(
    lambda n: st.lists(
        st.integers(min_value=1, max_value=12),
        min_size=n,
        max_size=n,
        unique=True,
    )
)

# Valid subject: non-empty string
subject_strategy = st.sampled_from([
    "Matemáticas", "Lenguaje", "Ciencias Naturales", "Ciencias Sociales",
    "Arte", "Educación Física", "Tecnología", "Inglés",
])

# Available resources list
resources_strategy = st.lists(
    st.sampled_from([
        "pizarra", "cuadernos", "lápices", "marcadores", "cartulina",
        "tijeras", "pegamento", "material reciclable", "computador",
    ]),
    min_size=0,
    max_size=5,
    unique=True,
)

# Node names in expected order
NODE_NAMES = [
    "curriculum_analysis",
    "activity_design",
    "resource_adaptation",
    "output_formatting",
]


# --- Helpers ---

def _make_variant_json(grade: int) -> str:
    """Create a valid JSON variant string for a given grade."""
    return json.dumps({
        "content": f"Contenido para grado {grade}",
        "instructions": f"Instrucciones para grado {grade}",
        "exercises": f"Ejercicios para grado {grade}",
    })


def _make_standards_for_grades(grades: list[int]) -> list[CurriculumStandard]:
    """Create curriculum standards (one per grade) for testing."""
    return [
        CurriculumStandard(
            country="CO",
            grade=g,
            subject="Matemáticas",
            text=f"Estándar curricular para grado {g}",
            similarity_score=0.85,
        )
        for g in grades
    ]


def _build_mock_node_functions(grades: list[int], execution_order: list[str]):
    """Build mock functions for each node that track execution order.

    Returns a dict of node_name -> async mock function.
    """
    standards = _make_standards_for_grades(grades)

    # Capture the real output_formatting.run before any patching
    _real_output_formatting_run = output_formatting.run

    async def mock_curriculum_analysis(state):
        execution_order.append("curriculum_analysis")
        return {
            "curriculum_standards": standards,
            "current_node": "curriculum_analysis",
        }

    async def mock_activity_design(state):
        execution_order.append("activity_design")
        return {
            "anchor_activity_draft": "Actividad ancla de prueba",
            "variants_draft": {g: _make_variant_json(g) for g in grades},
            "current_node": "activity_design",
        }

    async def mock_resource_adaptation(state):
        execution_order.append("resource_adaptation")
        return {
            "anchor_activity_adapted": "Actividad ancla adaptada",
            "variants_adapted": {g: _make_variant_json(g) for g in grades},
            "current_node": "resource_adaptation",
        }

    async def mock_output_formatting(state):
        execution_order.append("output_formatting")
        # Call the real output_formatting (captured before patching)
        return await _real_output_formatting_run(state)

    return {
        "curriculum_analysis": mock_curriculum_analysis,
        "activity_design": mock_activity_design,
        "resource_adaptation": mock_resource_adaptation,
        "output_formatting": mock_output_formatting,
    }


class TestPropertyStructuralInvariant:
    """Property 1: Invariante estructural de salida.

    **Validates: Requirements 1.1, 2.5**

    For any valid generation request with N grades (2 ≤ N ≤ 6), a non-empty
    topic, and a subject, the agent output SHALL contain exactly one anchor
    activity and exactly N variants, and the complete output SHALL validate
    against the ActivityOutput Pydantic schema.
    """

    @given(
        topic=topic_strategy,
        grades=grades_strategy,
        subject=subject_strategy,
        resources=resources_strategy,
    )
    @settings(max_examples=15)
    @pytest.mark.asyncio
    async def test_output_has_one_anchor_and_n_variants(
        self, topic: str, grades: list[int], subject: str, resources: list[str]
    ):
        """The graph output has exactly 1 anchor activity and N variants."""
        execution_order: list[str] = []
        mocks = _build_mock_node_functions(grades, execution_order)

        with (
            patch(
                "app.agent.nodes.curriculum_analysis.run",
                side_effect=mocks["curriculum_analysis"],
            ),
            patch(
                "app.agent.nodes.activity_design.run",
                side_effect=mocks["activity_design"],
            ),
            patch(
                "app.agent.nodes.resource_adaptation.run",
                side_effect=mocks["resource_adaptation"],
            ),
        ):
            graph = build_activity_graph()
            initial_state = {
                "topic": topic,
                "grades": sorted(grades),
                "subject": subject,
                "available_resources": resources,
                "curriculum_standards": [],
                "anchor_activity_draft": None,
                "variants_draft": None,
                "anchor_activity_adapted": None,
                "variants_adapted": None,
                "final_output": None,
                "current_node": "",
                "error": None,
            }

            result = await graph.ainvoke(initial_state)

        # The output should exist without errors
        assert result.get("error") is None, f"Unexpected error: {result.get('error')}"
        final_output = result["final_output"]
        assert final_output is not None

        # Validate against Pydantic schema
        assert isinstance(final_output, ActivityOutput)

        # Exactly one anchor activity (non-empty string)
        assert isinstance(final_output.anchor_activity, str)
        assert len(final_output.anchor_activity) > 0

        # Exactly N variants (one per grade)
        n = len(grades)
        assert len(final_output.variants) == n

        # Each variant corresponds to a grade from the input
        variant_grades = {v.grade for v in final_output.variants}
        assert variant_grades == set(grades)


class TestPropertySequentialExecution:
    """Property 2: Orden secuencial de ejecución de nodos.

    **Validates: Requirements 2.1**

    The graph SHALL execute nodes in order: curriculum_analysis →
    activity_design → resource_adaptation → output_formatting.
    """

    @given(
        topic=topic_strategy,
        grades=grades_strategy,
        subject=subject_strategy,
    )
    @settings(max_examples=10)
    @pytest.mark.asyncio
    async def test_nodes_execute_in_sequential_order(
        self, topic: str, grades: list[int], subject: str
    ):
        """Nodes execute in the exact order defined by the graph."""
        execution_order: list[str] = []
        mocks = _build_mock_node_functions(grades, execution_order)

        with (
            patch(
                "app.agent.nodes.curriculum_analysis.run",
                side_effect=mocks["curriculum_analysis"],
            ),
            patch(
                "app.agent.nodes.activity_design.run",
                side_effect=mocks["activity_design"],
            ),
            patch(
                "app.agent.nodes.resource_adaptation.run",
                side_effect=mocks["resource_adaptation"],
            ),
            patch(
                "app.agent.nodes.output_formatting.run",
                side_effect=mocks["output_formatting"],
            ),
        ):
            graph = build_activity_graph()
            initial_state = {
                "topic": topic,
                "grades": sorted(grades),
                "subject": subject,
                "available_resources": ["pizarra"],
                "curriculum_standards": [],
                "anchor_activity_draft": None,
                "variants_draft": None,
                "anchor_activity_adapted": None,
                "variants_adapted": None,
                "final_output": None,
                "current_node": "",
                "error": None,
            }

            await graph.ainvoke(initial_state)

        # Verify all 4 nodes executed in the correct order
        assert execution_order == NODE_NAMES, (
            f"Expected order {NODE_NAMES}, got {execution_order}"
        )


class TestPropertyNodeErrorIdentification:
    """Property 3: Identificación de nodo en errores.

    **Validates: Requirements 2.6**

    If a node fails, the error message SHALL identify which node failed
    (error starts with node name).
    """

    @given(
        topic=topic_strategy,
        grades=grades_strategy,
        subject=subject_strategy,
        failing_node=st.sampled_from(NODE_NAMES),
    )
    @settings(max_examples=12)
    @pytest.mark.asyncio
    async def test_error_message_starts_with_node_name(
        self, topic: str, grades: list[int], subject: str, failing_node: str
    ):
        """Error messages start with the name of the failing node."""
        execution_order: list[str] = []
        mocks = _build_mock_node_functions(grades, execution_order)

        # Replace the selected node with one that returns an error
        error_msg = f"{failing_node}: simulated test error"

        async def mock_failing_node(state):
            execution_order.append(failing_node)
            # Build a return dict with an error, matching node patterns
            if failing_node == "curriculum_analysis":
                return {
                    "curriculum_standards": [],
                    "current_node": "curriculum_analysis",
                    "error": error_msg,
                }
            elif failing_node == "activity_design":
                return {
                    "anchor_activity_draft": None,
                    "variants_draft": None,
                    "current_node": "activity_design",
                    "error": error_msg,
                }
            elif failing_node == "resource_adaptation":
                return {
                    "anchor_activity_adapted": None,
                    "variants_adapted": None,
                    "current_node": "resource_adaptation",
                    "error": error_msg,
                }
            else:  # output_formatting
                return {
                    "final_output": None,
                    "current_node": "output_formatting",
                    "error": error_msg,
                }

        # Build patches - the failing node gets the error mock,
        # others get their normal mocks
        patches = {}
        for node_name in NODE_NAMES:
            if node_name == failing_node:
                patches[node_name] = mock_failing_node
            else:
                patches[node_name] = mocks[node_name]

        with (
            patch(
                "app.agent.nodes.curriculum_analysis.run",
                side_effect=patches["curriculum_analysis"],
            ),
            patch(
                "app.agent.nodes.activity_design.run",
                side_effect=patches["activity_design"],
            ),
            patch(
                "app.agent.nodes.resource_adaptation.run",
                side_effect=patches["resource_adaptation"],
            ),
            patch(
                "app.agent.nodes.output_formatting.run",
                side_effect=patches["output_formatting"],
            ),
        ):
            graph = build_activity_graph()
            initial_state = {
                "topic": topic,
                "grades": sorted(grades),
                "subject": subject,
                "available_resources": ["pizarra"],
                "curriculum_standards": [],
                "anchor_activity_draft": None,
                "variants_draft": None,
                "anchor_activity_adapted": None,
                "variants_adapted": None,
                "final_output": None,
                "current_node": "",
                "error": None,
            }

            result = await graph.ainvoke(initial_state)

        # The error field should be set and start with the failing node name
        assert result.get("error") is not None, "Expected an error in state"
        assert result["error"].startswith(failing_node), (
            f"Error '{result['error']}' should start with node name '{failing_node}'"
        )


class TestPropertyVariantStandardAlignment:
    """Property 6: Alineación variante-estándar.

    **Validates: Requirements 1.4**

    Each variant's aligned_standards SHALL only contain standards whose
    grade matches that variant's grade.
    """

    @given(
        grades=grades_strategy,
        extra_standards_grades=st.lists(
            st.integers(min_value=1, max_value=12),
            min_size=0,
            max_size=10,
        ),
    )
    @settings(max_examples=15)
    @pytest.mark.asyncio
    async def test_aligned_standards_match_variant_grade(
        self, grades: list[int], extra_standards_grades: list[int]
    ):
        """Each variant only gets standards that match its grade."""
        # Build standards for the requested grades plus some extras
        all_standard_grades = list(set(grades + extra_standards_grades))
        standards = _make_standards_for_grades(all_standard_grades)

        # Build a state that output_formatting can process directly
        variants_adapted = {g: _make_variant_json(g) for g in grades}

        state = {
            "topic": "Tema de prueba",
            "grades": sorted(grades),
            "subject": "Matemáticas",
            "available_resources": ["pizarra"],
            "curriculum_standards": standards,
            "anchor_activity_adapted": "Actividad ancla adaptada",
            "variants_adapted": variants_adapted,
            "current_node": "resource_adaptation",
            "error": None,
        }

        # Call output_formatting directly (it's a pure function)
        result = await output_formatting.run(state)

        assert result.get("error") is None, f"Unexpected error: {result.get('error')}"
        final_output: ActivityOutput = result["final_output"]
        assert final_output is not None

        # For each variant, all aligned_standards must match the variant's grade
        for variant in final_output.variants:
            for std in variant.aligned_standards:
                assert std.grade == variant.grade, (
                    f"Standard with grade {std.grade} found in variant for "
                    f"grade {variant.grade}"
                )

    @given(
        grades=grades_strategy,
    )
    @settings(max_examples=10)
    @pytest.mark.asyncio
    async def test_variant_gets_standards_only_for_its_grade(
        self, grades: list[int]
    ):
        """Standards from other grades are NOT included in a variant."""
        # Create standards with distinctive text per grade
        standards = []
        for g in range(1, 13):
            standards.append(
                CurriculumStandard(
                    country="CO",
                    grade=g,
                    subject="Ciencias",
                    text=f"Estándar único grado {g}",
                    similarity_score=0.9,
                )
            )

        variants_adapted = {g: _make_variant_json(g) for g in grades}

        state = {
            "topic": "Ecosistemas",
            "grades": sorted(grades),
            "subject": "Ciencias",
            "available_resources": [],
            "curriculum_standards": standards,
            "anchor_activity_adapted": "Actividad ancla",
            "variants_adapted": variants_adapted,
            "current_node": "resource_adaptation",
            "error": None,
        }

        result = await output_formatting.run(state)

        assert result.get("error") is None
        final_output: ActivityOutput = result["final_output"]

        for variant in final_output.variants:
            # Each variant must have exactly one standard (for its grade)
            assert len(variant.aligned_standards) == 1, (
                f"Variant grade {variant.grade} has "
                f"{len(variant.aligned_standards)} standards, expected 1"
            )
            assert variant.aligned_standards[0].grade == variant.grade
