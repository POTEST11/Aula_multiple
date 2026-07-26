"""Document schemas for upload and retrieval responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Schema for document data in responses.

    Status values: pending | processing | ready | error
    """

    id: int
    classroom_id: int
    filename: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: str = Field(..., pattern=r"^(pending|processing|ready|error)$")
    error_message: str | None = None
    chunk_count: int | None = None
    uploaded_at: datetime
    processed_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentChunk(BaseModel):
    """A retrieved chunk from a class document."""

    content: str
    document_filename: str
    similarity_score: float
