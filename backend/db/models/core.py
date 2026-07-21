"""Core domain models: User, Category, Task.

Uses only portable SQLAlchemy types (String, JSON) so the models work
with both PostgreSQL (production) and SQLite (test / CI).
UUIDs are stored as String(36) — the default uuid4 string representation.
"""

import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # nullable for pure-OAuth accounts
    auth_provider = Column(String(32), nullable=True, index=True)    # e.g. "google", "github"
    auth_provider_id = Column(String(255), nullable=True, index=True)  # provider's user-id
    timezone = Column(String(50), nullable=False, server_default="UTC")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    planner_templates = relationship(
        "PlannerTemplate", back_populates="user", cascade="all, delete-orphan"
    )
    oauth_tokens = relationship(
        "UserOAuthToken",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    synced_events = relationship(
        "ExternalSyncedEvent", back_populates="user", cascade="all, delete-orphan"
    )
    ai_profile = relationship(
        "AIUserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    ai_recommendations = relationship(
        "AIRecommendation", back_populates="user", cascade="all, delete-orphan"
    )


class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=_uuid, index=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(50), nullable=False)
    color_hex = Column(String(7), server_default="#FFFFFF", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="categories")
    tasks = relationship("Task", back_populates="category")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=_uuid, index=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = Column(
        String(36),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, server_default="1", nullable=False)
    status = Column(String(20), server_default="pending", nullable=False)
    checklist = Column(JSON, server_default="[]", nullable=False)
    source_template_name = Column(String(100), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="tasks")
    category = relationship("Category", back_populates="tasks")