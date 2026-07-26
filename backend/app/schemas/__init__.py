"""Pydantic schemas for request/response validation."""

from .activity import (
    ActivityOutput,
    CurriculumStandard,
    GenerateRequest,
    VariantOutput,
)
from .auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from .classroom import ClassroomCreate, ClassroomResponse, ClassroomUpdate
from .document import DocumentChunk, DocumentResponse
from .history import HistorySummary
from .subject import SubjectCreate, SubjectResponse

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    # Activity
    "GenerateRequest",
    "CurriculumStandard",
    "VariantOutput",
    "ActivityOutput",
    # Classroom
    "ClassroomCreate",
    "ClassroomUpdate",
    "ClassroomResponse",
    # Document
    "DocumentResponse",
    "DocumentChunk",
    # Subject
    "SubjectCreate",
    "SubjectResponse",
    # History
    "HistorySummary",
]
