"""Classroom model."""

from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import relationship

from .base import Base


class Classroom(Base):
    """A multi-grade classroom belonging to a teacher."""

    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    grades = Column(ARRAY(Integer), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="classrooms")
    activities = relationship("Activity", back_populates="classroom")
    documents = relationship(
        "ClassDocument", back_populates="classroom", cascade="all, delete-orphan"
    )
