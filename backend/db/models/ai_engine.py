"""AI engine models: AIUserProfile, AIRecommendation.

Portable types only (no JSONB/UUID) for SQLite / CI compatibility.
"""

import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base, PortableUUID


def _uuid() -> str:
    return str(uuid.uuid4())




class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recommendation_text = Column(Text, nullable=False)
    rationale = Column(Text, nullable=True)
    suggested_changes = Column(JSON, nullable=False, server_default="{}")
    status = Column(String(20), server_default="pending", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="ai_recommendations")