"""Classroom schemas for CRUD operations."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ClassroomCreate(BaseModel):
    """Schema for creating a classroom.

    Same grade validation as GenerateRequest: 2-6 elements, each 1-12, no duplicates.
    """

    name: str = Field(..., min_length=1, max_length=255)
    grades: list[int] = Field(..., min_length=2, max_length=6)

    @field_validator("grades")
    @classmethod
    def validate_grades(cls, v: list[int]) -> list[int]:
        if not all(1 <= g <= 12 for g in v):
            raise ValueError("Cada grado debe estar entre 1 y 12")
        if len(v) != len(set(v)):
            raise ValueError("Los grados no deben repetirse")
        return sorted(v)


class ClassroomUpdate(BaseModel):
    """Schema for updating a classroom. All fields optional."""

    name: str | None = Field(None, min_length=1, max_length=255)
    grades: list[int] | None = Field(None, min_length=2, max_length=6)

    @field_validator("grades")
    @classmethod
    def validate_grades(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return v
        if not all(1 <= g <= 12 for g in v):
            raise ValueError("Cada grado debe estar entre 1 y 12")
        if len(v) != len(set(v)):
            raise ValueError("Los grados no deben repetirse")
        return sorted(v)


class ClassroomResponse(BaseModel):
    """Schema for classroom data in responses."""

    id: int
    name: str
    grades: list[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
