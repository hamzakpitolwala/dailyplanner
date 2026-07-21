import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base


class PlannerTemplate(Base):
    __tablename__ = "planner_templates"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="planner_templates")
    template_tasks = relationship(
        "TemplateTask",
        back_populates="planner_template",
        cascade="all, delete-orphan",
    )


class TemplateTask(Base):
    __tablename__ = "template_tasks"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("planner_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, server_default="1", nullable=False)
    category_label = Column(String(50), nullable=True)
    relative_day_offset = Column(Integer, server_default="0", nullable=False)
    target_time = Column(Time, nullable=True)
    checklist = Column(JSONB, server_default="[]", nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    planner_template = relationship("PlannerTemplate", back_populates="template_tasks")