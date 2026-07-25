"""Activity, ActivityVariant, and VariantStandard models."""

from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from .base import Base


class Activity(Base):
    """A generated pedagogical activity with anchor content."""

    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    topic = Column(String(500), nullable=False)
    grades = Column(ARRAY(Integer), nullable=False)
    subject_name = Column(String(255), nullable=False)
    classroom_name = Column(String(255), nullable=True)
    available_resources = Column(ARRAY(String), nullable=True)
    anchor_activity = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="activities")
    classroom = relationship("Classroom", back_populates="activities")
    subject = relationship("Subject", back_populates="activities")
    variants = relationship(
        "ActivityVariant", back_populates="activity", cascade="all, delete-orphan"
    )


class ActivityVariant(Base):
    """A grade-specific variant of an activity."""

    __tablename__ = "activity_variants"

    id = Column(Integer, primary_key=True)
    activity_id = Column(
        Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False
    )
    grade = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    instructions = Column(Text, nullable=False)
    exercises = Column(Text, nullable=False)

    # Relationships
    activity = relationship("Activity", back_populates="variants")
    standards = relationship(
        "VariantStandard", back_populates="variant", cascade="all, delete-orphan"
    )


class VariantStandard(Base):
    """A curriculum standard reference linked to a variant."""

    __tablename__ = "variant_standards"

    id = Column(Integer, primary_key=True)
    variant_id = Column(
        Integer,
        ForeignKey("activity_variants.id", ondelete="CASCADE"),
        nullable=False,
    )
    curriculum_embedding_id = Column(
        Integer, ForeignKey("curriculum_embeddings.id"), nullable=True
    )
    standard_text = Column(Text, nullable=False)
    country = Column(String(100), nullable=False)
    grade = Column(Integer, nullable=False)
    subject = Column(String(255), nullable=False)

    # Relationships
    variant = relationship("ActivityVariant", back_populates="standards")
    curriculum_embedding = relationship("CurriculumEmbedding")
