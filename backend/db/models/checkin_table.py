"""Check-in models for activity status tracking."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base


class ActivityCheckin(Base):
    """Records a status change (check-in) on an activity."""

    __tablename__ = "activity_checkins"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(
        Integer,
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(32), nullable=False)  # done, not_done, partial, rescheduled
    notes = Column(Text, nullable=True)
    checked_in_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    activity = relationship("Activity", back_populates="checkins")
    missed_reason = relationship(
        "MissedReason",
        back_populates="checkin",
        uselist=False,
        cascade="all, delete-orphan",
    )
    alternate_activity = relationship(
        "AlternateActivity",
        back_populates="checkin",
        uselist=False,
        cascade="all, delete-orphan",
    )


class MissedReason(Base):
    """Structured reason for why an activity was not done."""

    __tablename__ = "missed_reasons"

    id = Column(Integer, primary_key=True, index=True)
    checkin_id = Column(
        Integer,
        ForeignKey("activity_checkins.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    reason_code = Column(String(64), nullable=False)
    free_text = Column(Text, nullable=True)

    checkin = relationship("ActivityCheckin", back_populates="missed_reason")


class AlternateActivity(Base):
    """What the user did instead when an activity was missed."""

    __tablename__ = "alternate_activities"

    id = Column(Integer, primary_key=True, index=True)
    checkin_id = Column(
        Integer,
        ForeignKey("activity_checkins.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    description = Column(Text, nullable=False)
    category = Column(String(80), nullable=True)

    checkin = relationship("ActivityCheckin", back_populates="alternate_activity")
