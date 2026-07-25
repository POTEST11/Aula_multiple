"""History schemas for activity listing."""

from datetime import datetime

from pydantic import BaseModel


class HistorySummary(BaseModel):
    """Schema for activity history list items (summary view)."""

    id: int
    topic: str
    grades: list[int]
    subject_name: str
    classroom_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
