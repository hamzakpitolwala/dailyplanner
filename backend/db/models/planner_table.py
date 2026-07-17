from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base


class DailyPlanner(Base):
    __tablename__ = "daily_planners"
    __table_args__ = (
        UniqueConstraint("user_id", "planner_date", name="uq_daily_planner_user_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    planner_date = Column(Date, nullable=False, index=True)
    title = Column(String(160), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User")
    activities = relationship(
        "Activity",
        back_populates="planner",
        cascade="all, delete-orphan",
        order_by="Activity.start_time",
    )


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    planner_id = Column(Integer, ForeignKey("daily_planners.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(80), nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    status = Column(String(32), default="planned", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    planner = relationship("DailyPlanner", back_populates="activities")
    policy = relationship(
        "ActivityPolicy",
        back_populates="activity",
        uselist=False,
        cascade="all, delete-orphan",
    )
    checkins = relationship(
        "ActivityCheckin",
        back_populates="activity",
        cascade="all, delete-orphan",
        order_by="ActivityCheckin.checked_in_at.desc()",
    )


class ActivityPolicy(Base):
    __tablename__ = "activity_policies"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, unique=True)
    requires_reason = Column(Boolean, default=True, nullable=False)
    allows_alternate = Column(Boolean, default=True, nullable=False)
    monitoring_allowed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    activity = relationship("Activity", back_populates="policy")
