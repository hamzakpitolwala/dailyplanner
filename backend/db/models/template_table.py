"""Models for reusable planner and activity templates."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base


class PlannerTemplate(Base):
    """A reusable blueprint for generating daily planners."""

    __tablename__ = "planner_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(160), nullable=False)
    in_use = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User")
    activity_templates = relationship(
        "ActivityTemplate",
        back_populates="planner_template",
        cascade="all, delete-orphan",
        order_by="ActivityTemplate.start_time",
    )


class ActivityTemplate(Base):
    """A blueprint for a single activity within a planner template."""

    __tablename__ = "activity_templates"

    id = Column(Integer, primary_key=True, index=True)
    planner_template_id = Column(
        Integer,
        ForeignKey("planner_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(80), nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    planner_template = relationship("PlannerTemplate", back_populates="activity_templates")
    # A simplified version of policy can also be added here if needed, but for now we default policies on generation.
