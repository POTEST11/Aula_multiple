"""ClassDocument model for uploaded classroom documents."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship

from .base import Base


class ClassDocument(Base):
    """A document uploaded by a teacher and associated to a classroom."""

    __tablename__ = "class_documents"

    id = Column(Integer, primary_key=True)
    classroom_id = Column(
        Integer,
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending | processing | ready | error
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, nullable=True)
    uploaded_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    classroom = relationship("Classroom", back_populates="documents")
    user = relationship("User")
    embeddings = relationship(
        "DocumentEmbedding", back_populates="document", cascade="all, delete-orphan"
    )
