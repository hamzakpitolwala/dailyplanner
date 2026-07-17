"""History models for activity status tracking and state machine."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base


class ActivityHistoryEvent(Base):
    """Records an immutable state change or edit on an activity."""

    __tablename__ = "activity_history_events"

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
    action_type = Column(String(50), nullable=False) # "status_change", "edit", "reschedule", "creation"
    previous_state = Column(String(32), nullable=True)
    new_state = Column(String(32), nullable=False)
    
    notes = Column(Text, nullable=True) # General reason or notes
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    activity = relationship("Activity", back_populates="history_events")
    
    missed_reason = relationship(
        "MissedReason",
        back_populates="history_event",
        uselist=False,
        cascade="all, delete-orphan",
    )
    alternate_activity = relationship(
        "AlternateActivity",
        back_populates="history_event",
        uselist=False,
        cascade="all, delete-orphan",
    )


class MissedReason(Base):
    """Structured reason for why an activity was not done."""

    __tablename__ = "missed_reasons"

    id = Column(Integer, primary_key=True, index=True)
    history_event_id = Column(
        Integer,
        ForeignKey("activity_history_events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    reason_code = Column(String(64), nullable=False)
    free_text = Column(Text, nullable=True)

    history_event = relationship("ActivityHistoryEvent", back_populates="missed_reason")


class AlternateActivity(Base):
    """What the user did instead when an activity was missed."""

    __tablename__ = "alternate_activities"

    id = Column(Integer, primary_key=True, index=True)
    history_event_id = Column(
        Integer,
        ForeignKey("activity_history_events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    description = Column(Text, nullable=False)
    category = Column(String(80), nullable=True)

    history_event = relationship("ActivityHistoryEvent", back_populates="alternate_activity")
