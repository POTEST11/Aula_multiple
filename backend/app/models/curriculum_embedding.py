"""CurriculumEmbedding model with pgvector support."""

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, text

from pgvector.sqlalchemy import Vector

from .base import Base


class CurriculumEmbedding(Base):
    """Vectorized curriculum standard fragment for RAG retrieval."""

    __tablename__ = "curriculum_embeddings"

    id = Column(Integer, primary_key=True)
    country = Column(String(100), nullable=False, index=True)
    grade = Column(Integer, nullable=False, index=True)
    subject = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), unique=True, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    extra_metadata = Column("metadata", JSON, nullable=True)
    ingested_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
