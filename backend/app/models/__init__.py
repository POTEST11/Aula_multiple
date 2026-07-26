"""SQLAlchemy models package — import all models for convenient access."""

from .base import Base
from .user import User
from .classroom import Classroom
from .subject import Subject
from .activity import Activity, ActivityVariant, VariantStandard
from .curriculum_embedding import CurriculumEmbedding
from .class_document import ClassDocument
from .document_embedding import DocumentEmbedding

__all__ = [
    "Base",
    "User",
    "Classroom",
    "Subject",
    "Activity",
    "ActivityVariant",
    "VariantStandard",
    "CurriculumEmbedding",
    "ClassDocument",
    "DocumentEmbedding",
]
