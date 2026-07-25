"""Activity generation schemas for request and response."""

from pydantic import BaseModel, Field, field_validator


class GenerateRequest(BaseModel):
    """Schema for activity generation requests.

    Validates that grades list has 2-6 elements, each between 1-12,
    no duplicates, and returns them sorted.
    """

    topic: str = Field(..., min_length=3, max_length=500)
    classroom_id: int | None = None
    subject_id: int | None = None
    grades: list[int] = Field(..., min_length=2, max_length=6)
    subject_name: str = Field(..., min_length=1, max_length=255)
    available_resources: list[str] | None = None

    @field_validator("grades")
    @classmethod
    def validate_grades(cls, v: list[int]) -> list[int]:
        if not all(1 <= g <= 12 for g in v):
            raise ValueError("Cada grado debe estar entre 1 y 12")
        if len(v) != len(set(v)):
            raise ValueError("Los grados no deben repetirse")
        return sorted(v)


class CurriculumStandard(BaseModel):
    """A curriculum standard retrieved from RAG."""

    country: str
    grade: int
    subject: str
    text: str
    similarity_score: float | None = None


class VariantOutput(BaseModel):
    """A grade-specific variant in the activity output."""

    grade: int
    content: str
    instructions: str
    exercises: str
    aligned_standards: list[CurriculumStandard]


class ActivityOutput(BaseModel):
    """Complete activity output with anchor and variants."""

    id: int | None = None
    topic: str
    grades: list[int]
    subject_name: str
    classroom_name: str | None = None
    available_resources: list[str]
    anchor_activity: str
    variants: list[VariantOutput]
    created_at: str | None = None

    model_config = {"from_attributes": True}
