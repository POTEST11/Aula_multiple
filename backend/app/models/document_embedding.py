"""DocumentEmbedding model with pgvector support for class documents."""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from pgvector.sqlalchemy import Vector

from .base import Base


class DocumentEmbedding(Base):
    """Vectorized chunk from a class document for RAG retrieval."""

    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True)
    document_id = Column(
        Integer,
        ForeignKey("class_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    classroom_id = Column(
        Integer,
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationships
    document = relationship("ClassDocument", back_populates="embeddings")

    # Constraints
    __table_args__ = (
        UniqueConstraint("document_id", "content_hash", name="uq_doc_chunk_hash"),
        Index("ix_doc_embed_classroom", "classroom_id"),
    )
