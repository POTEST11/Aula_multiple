"""Subject schemas for CRUD operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    """Schema for creating a subject."""

    name: str = Field(..., min_length=1, max_length=255)


class SubjectResponse(BaseModel):
    """Schema for subject data in responses."""

    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
