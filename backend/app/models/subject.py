"""Subject model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import relationship

from .base import Base


class Subject(Base):
    """A curricular subject registered by a teacher."""

    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="subjects")
    activities = relationship("Activity", back_populates="subject")
