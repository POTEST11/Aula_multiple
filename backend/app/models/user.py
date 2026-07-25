"""User model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, text
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    """Authenticated teacher account."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationships
    classrooms = relationship("Classroom", back_populates="user")
    subjects = relationship("Subject", back_populates="user")
    activities = relationship("Activity", back_populates="user")
