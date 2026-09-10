import uuid
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY, TEXT

from backend.db.database import Base, PortableUUID


class PortableScopes(TypeDecorator):
    """
    Portable scopes column type.
    Maps to ARRAY(TEXT) on PostgreSQL and JSON on SQLite.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load dialect impl."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(TEXT))
        else:
            return dialect.type_descriptor(JSON)


def _uuid() -> str:
    """ uuid."""
    return str(uuid.uuid4())


class UserOAuthToken(Base):
    """Useroauthtoken."""
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
    scopes = Column(PortableScopes, nullable=False, default=list)   # list[str] as JSON or ARRAY
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
    """Externalsyncedevent."""
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
    calendar_id = Column(String(255), server_default="primary", nullable=False)
    event_type = Column(String(50), nullable=False, server_default="calendar_event")
    parsed_summary = Column(Text, nullable=False, server_default="")
    summary = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    location = Column(Text, nullable=True)
    status = Column(String(50), server_default="confirmed", nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    raw_payload = Column(JSON, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="synced_events")
    tasks = relationship("Task", back_populates="external_event")

    __table_args__ = (
        UniqueConstraint("user_id", "external_id", name="uq_user_external_event"),
    )
