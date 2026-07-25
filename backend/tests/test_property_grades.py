"""Property-based tests for grade validation (Property 11).

**Validates: Requirements 5.1, 8.3**

Property 11: For any grade list with length < 2 or > 6, or with values
outside range 1-12, or with duplicates, classroom creation or generation
request SHALL be rejected with a validation error before processing.
Conversely, valid grade lists (2-6 unique integers in 1-12) are accepted
and returned sorted.
"""

import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.schemas.classroom import ClassroomCreate
from app.schemas.activity import GenerateRequest


# --- Strategies ---

# Valid grades: 2-6 unique integers from 1-12, returned sorted
valid_grades_strategy = st.integers(min_value=2, max_value=6).flatmap(
    lambda n: st.lists(
        st.integers(min_value=1, max_value=12),
        min_size=n,
        max_size=n,
        unique=True,
    )
)

# Invalid: too few grades (0 or 1 element)
too_few_grades_strategy = st.lists(
    st.integers(min_value=1, max_value=12),
    min_size=0,
    max_size=1,
    unique=True,
)

# Invalid: too many grades (7-12 elements, unique in 1-12)
too_many_grades_strategy = st.integers(min_value=7, max_value=12).flatmap(
    lambda n: st.lists(
        st.integers(min_value=1, max_value=12),
        min_size=n,
        max_size=n,
        unique=True,
    )
)

# Invalid: grades out of range (at least one grade < 1 or > 12)
out_of_range_grades_strategy = st.lists(
    st.integers(min_value=1, max_value=12),
    min_size=1,
    max_size=5,
    unique=True,
).flatmap(
    lambda valid: st.one_of(
        st.integers(max_value=0),
        st.integers(min_value=13),
    ).map(lambda bad: valid + [bad])
)

# Invalid: grades with duplicates (2-6 elements, at least one repeated)
duplicate_grades_strategy = st.lists(
    st.integers(min_value=1, max_value=12),
    min_size=2,
    max_size=5,
    unique=True,
).flatmap(
    lambda unique_list: st.sampled_from(unique_list).map(
        lambda dup: unique_list + [dup]
    )
)


class TestGradeValidationProperty:
    """Property 11: Validación de rango de grados.

    **Validates: Requirements 5.1, 8.3**
    """

    # --- Valid grades accepted and sorted ---

    @given(grades=valid_grades_strategy)
    @settings(max_examples=100)
    def test_valid_grades_accepted_classroom(self, grades: list[int]):
        """Valid grades (2-6 unique ints in 1-12) are accepted by ClassroomCreate
        and returned sorted."""
        classroom = ClassroomCreate(name="Test Class", grades=grades)
        assert classroom.grades == sorted(grades)
        assert len(classroom.grades) == len(grades)
        assert all(1 <= g <= 12 for g in classroom.grades)

    @given(grades=valid_grades_strategy)
    @settings(max_examples=100)
    def test_valid_grades_accepted_generate_request(self, grades: list[int]):
        """Valid grades (2-6 unique ints in 1-12) are accepted by GenerateRequest
        and returned sorted."""
        request = GenerateRequest(
            topic="Matemáticas básicas",
            grades=grades,
            subject_name="Matemáticas",
        )
        assert request.grades == sorted(grades)
        assert len(request.grades) == len(grades)
        assert all(1 <= g <= 12 for g in request.grades)

    # --- Invalid: too few grades ---

    @given(grades=too_few_grades_strategy)
    @settings(max_examples=50)
    def test_too_few_grades_rejected_classroom(self, grades: list[int]):
        """Grade lists with fewer than 2 elements are rejected."""
        with pytest.raises(ValidationError):
            ClassroomCreate(name="Test Class", grades=grades)

    @given(grades=too_few_grades_strategy)
    @settings(max_examples=50)
    def test_too_few_grades_rejected_generate_request(self, grades: list[int]):
        """Grade lists with fewer than 2 elements are rejected."""
        with pytest.raises(ValidationError):
            GenerateRequest(
                topic="Tema de prueba",
                grades=grades,
                subject_name="Ciencias",
            )

    # --- Invalid: too many grades ---

    @given(grades=too_many_grades_strategy)
    @settings(max_examples=50)
    def test_too_many_grades_rejected_classroom(self, grades: list[int]):
        """Grade lists with more than 6 elements are rejected."""
        with pytest.raises(ValidationError):
            ClassroomCreate(name="Test Class", grades=grades)

    @given(grades=too_many_grades_strategy)
    @settings(max_examples=50)
    def test_too_many_grades_rejected_generate_request(self, grades: list[int]):
        """Grade lists with more than 6 elements are rejected."""
        with pytest.raises(ValidationError):
            GenerateRequest(
                topic="Tema de prueba",
                grades=grades,
                subject_name="Ciencias",
            )

    # --- Invalid: out of range ---

    @given(grades=out_of_range_grades_strategy)
    @settings(max_examples=50)
    def test_out_of_range_grades_rejected_classroom(self, grades: list[int]):
        """Grades outside 1-12 range are rejected."""
        assume(2 <= len(grades) <= 6)
        with pytest.raises(ValidationError):
            ClassroomCreate(name="Test Class", grades=grades)

    @given(grades=out_of_range_grades_strategy)
    @settings(max_examples=50)
    def test_out_of_range_grades_rejected_generate_request(self, grades: list[int]):
        """Grades outside 1-12 range are rejected."""
        assume(2 <= len(grades) <= 6)
        with pytest.raises(ValidationError):
            GenerateRequest(
                topic="Tema de prueba",
                grades=grades,
                subject_name="Ciencias",
            )

    # --- Invalid: duplicates ---

    @given(grades=duplicate_grades_strategy)
    @settings(max_examples=50)
    def test_duplicate_grades_rejected_classroom(self, grades: list[int]):
        """Grade lists with duplicates are rejected."""
        assume(2 <= len(grades) <= 6)
        with pytest.raises(ValidationError):
            ClassroomCreate(name="Test Class", grades=grades)

    @given(grades=duplicate_grades_strategy)
    @settings(max_examples=50)
    def test_duplicate_grades_rejected_generate_request(self, grades: list[int]):
        """Grade lists with duplicates are rejected."""
        assume(2 <= len(grades) <= 6)
        with pytest.raises(ValidationError):
            GenerateRequest(
                topic="Tema de prueba",
                grades=grades,
                subject_name="Ciencias",
            )
