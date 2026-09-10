"""Core domain models: User, Category, Task.

Uses only portable SQLAlchemy types (String, JSON) so the models work
with both PostgreSQL (production) and SQLite (test / CI).
UUIDs are stored as PortableUUID — the default uuid4 string representation.
"""

import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base, PortableUUID


def _uuid() -> str:
    """ uuid."""
    return str(uuid.uuid4())


class User(Base):
    """User."""
    __tablename__ = "users"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
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
    planner_templates = relationship("PlannerTemplate", back_populates="user", cascade="all, delete-orphan"
    )
    oauth_tokens = relationship("UserOAuthToken",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    synced_events = relationship("ExternalSyncedEvent", back_populates="user", cascade="all, delete-orphan"
    )
    user_profile = relationship("UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    ai_recommendations = relationship("AIRecommendation", back_populates="user", cascade="all, delete-orphan"
    )
    ai_profile = relationship("AIUserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    fixed_blocks = relationship("FixedBlock", back_populates="user", cascade="all, delete-orphan"
    )


class Category(Base):
    """Category."""
    __tablename__ = "categories"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
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
    """Task."""
    __tablename__ = "tasks"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = Column(
        PortableUUID,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, server_default="1", nullable=False)
    status = Column(String(20), server_default="pending", nullable=False, index=True)
    checklist = Column(JSON, server_default="[]", nullable=False)
    source_template_id = Column(String(36), nullable=True)
    source_template_task_id = Column(String(36), nullable=True)
    source_template_name = Column(String(255), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True) # acts as end_time
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    requires_reason = Column(Integer, server_default="0", nullable=False)  # boolean SQLite compat
    allows_alternate = Column(Integer, server_default="0", nullable=False)

    # Phase 6 Google Calendar / external event extensions
    source = Column(String(20), server_default="manual", nullable=False, index=True)  # 'template', 'manual', 'calendar'
    external_event_id = Column(
        PortableUUID,
        ForeignKey("external_synced_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    visibility = Column(String(20), server_default="normal", nullable=False, index=True)  # 'normal', 'planner-only', 'hidden'

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
    checkins = relationship("TaskCheckin", back_populates="task", cascade="all, delete-orphan")
    subtasks = relationship("ActivitySubtask", back_populates="task", cascade="all, delete-orphan")
    external_event = relationship("ExternalSyncedEvent", back_populates="tasks")


class ActivitySubtask(Base):
    """Activitysubtask."""
    __tablename__ = "activity_subtasks"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    task_id = Column(
        PortableUUID,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    is_completed = Column(Integer, server_default="0", nullable=False)  # boolean SQLite compat
    is_template_subtask = Column(Integer, server_default="0", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    task = relationship("Task", back_populates="subtasks")


class MissedReason(Base):
    """Missedreason."""
    __tablename__ = "missed_reasons"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # null means global default
        index=True,
    )
    name = Column(String(255), nullable=False)


class AlternateActivity(Base):
    """Alternateactivity."""
    __tablename__ = "alternate_activities"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # null means global default
        index=True,
    )
    name = Column(String(255), nullable=False)


class TaskCheckin(Base):
    """Taskcheckin."""
    __tablename__ = "task_checkins"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    task_id = Column(
        PortableUUID,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(20), nullable=False)  # done, not_done, partial, rescheduled
    missed_reason_id = Column(
        PortableUUID,
        ForeignKey("missed_reasons.id", ondelete="SET NULL"),
        nullable=True,
    )
    alternate_activity_id = Column(
        PortableUUID,
        ForeignKey("alternate_activities.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    task = relationship("Task", back_populates="checkins")
    missed_reason = relationship("MissedReason")
    alternate_activity = relationship("AlternateActivity")


class UserProfile(Base):
    """Userprofile."""
    __tablename__ = "user_profiles"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    username = Column(String(255), unique=True, nullable=True, index=True)
    dob = Column(String(50), nullable=True)
    gender = Column(String(50), nullable=True)
    goals = Column(String(255), nullable=True)
    focus_times = Column(String(255), nullable=True)
    typical_disruptions = Column(String(255), nullable=True)
    structure_preference = Column(String(255), nullable=True)
    ai_guidance_level = Column(String(255), nullable=True)
    onboarding_completed = Column(Integer, server_default="0", nullable=False) # boolean

    active_planner_id = Column(
        PortableUUID,
        ForeignKey("planner_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_login_date = Column(String(10), nullable=True) # YYYY-MM-DD

    # AI engine fields (merged)
    personality_type = Column(String(50), nullable=True)
    productivity_velocity = Column(Float, server_default="1.0", nullable=False)
    ai_inferred_traits = Column(JSON, nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="user_profile")


class FixedBlock(Base):
    """Fixedblock."""
    __tablename__ = "fixed_blocks"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    start_time = Column(String(5), nullable=False)  # "HH:MM"
    end_time = Column(String(5), nullable=False)    # "HH:MM"
    days_of_week = Column(JSON, nullable=False)     # e.g., [1, 2, 3, 4, 5]
    apply_all = Column(Integer, server_default="1", nullable=False)
    template_ids = Column(JSON, nullable=False, server_default="'[]'")

    # Relationships
    user = relationship("User", back_populates="fixed_blocks")


class MonitoringSession(Base):
    """Monitoringsession."""
    __tablename__ = "monitoring_sessions"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_id = Column(
        PortableUUID,
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ScreenEvent(Base):
    """Screenevent."""
    __tablename__ = "screen_events"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    session_id = Column(
        PortableUUID,
        ForeignKey("monitoring_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    app_name = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True)
    duration_seconds = Column(Integer, server_default="0", nullable=False)
    is_blocked = Column(Integer, server_default="0", nullable=False) # boolean
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FeatureFlag(Base):
    """Featureflag."""
    __tablename__ = "feature_flags"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    enabled_global = Column(Integer, server_default="0", nullable=False) # boolean
    rollout_percentage = Column(Integer, server_default="0", nullable=False)
    description = Column(String(255), nullable=True)
