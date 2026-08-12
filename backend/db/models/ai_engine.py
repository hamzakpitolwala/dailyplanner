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


class AIUserProfile(Base):
    __tablename__ = "ai_user_profiles"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    personality_type = Column(String(50), nullable=True)
    productivity_velocity = Column(Float, server_default="1.0", nullable=False)
    ai_inferred_traits = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="ai_profile")


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind = Column(String(50), nullable=False) # e.g. move_activity_time
    scope = Column(String(50), nullable=False) # template | daily_instance | activity | global
    
    target_template_id = Column(PortableUUID, ForeignKey("planner_templates.id", ondelete="SET NULL"), nullable=True)
    target_daily_planner_id = Column(PortableUUID, nullable=True) # transient daily planner ref
    target_activity_id = Column(PortableUUID, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    
    payload = Column(JSON, nullable=False, server_default="{}")
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=True)
    status = Column(String(20), server_default="pending", nullable=False)
    source_period_start = Column(String(20), nullable=True) # YYYY-MM-DD
    source_period_end = Column(String(20), nullable=True)   # YYYY-MM-DD
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="ai_recommendations")
    outcomes = relationship("RecommendationOutcome", back_populates="recommendation", cascade="all, delete-orphan")


class RecommendationOutcome(Base):
    __tablename__ = "recommendation_outcomes"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    recommendation_id = Column(
        PortableUUID,
        ForeignKey("ai_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision = Column(String(20), nullable=False) # accepted, rejected, ignored
    decided_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    applied_change_ref = Column(JSON, nullable=True)

    # Relationships
    recommendation = relationship("AIRecommendation", back_populates="outcomes")
    user = relationship("User")

class AISummary(Base):
    __tablename__ = "ai_summaries"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_type = Column(String(20), nullable=False) # 'week'
    period_start = Column(String(20), nullable=False) # YYYY-MM-DD
    period_end = Column(String(20), nullable=False)   # YYYY-MM-DD
    summary_text = Column(Text, nullable=False)
    wins = Column(JSON, nullable=False, server_default="[]")
    issues = Column(JSON, nullable=False, server_default="[]")
    suggestions = Column(JSON, nullable=False, server_default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User")