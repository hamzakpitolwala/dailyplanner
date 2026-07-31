"""Integration / OAuth token models.

Portable types only (no JSONB/ARRAY/UUID) for SQLite / CI compatibility.
The `scopes` field is stored as a JSON list instead of Postgres ARRAY(Text).
"""

import uuid
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.database import Base, PortableUUID


def _uuid() -> str:
    return str(uuid.uuid4())


class UserOAuthToken(Base):
    __tablename__ = "user_oauth_tokens"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    provider = Column(String(50), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    scopes = Column(JSON, nullable=False, server_default="[]")   # list[str] as JSON
    expires_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="oauth_tokens")


class ExternalSyncedEvent(Base):
    __tablename__ = "external_synced_events"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_provider = Column(String(50), nullable=False)
    external_id = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)
    parsed_summary = Column(Text, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="synced_events")

    __table_args__ = (
        UniqueConstraint("user_id", "external_id", name="uq_user_external_event"),
    )