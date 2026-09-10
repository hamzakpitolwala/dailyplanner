from typing import Any
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON, Boolean, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.db.database import Base, PortableUUID

import uuid

def _uuid() -> str:
    """ uuid."""
    return str(uuid.uuid4())

class WorkflowRun(Base):
    """Workflowrun."""
    __tablename__ = "workflow_runs"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(
        PortableUUID,
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    state = Column(String(50), nullable=False, default="RECEIVED")
    intents = Column(JSON, nullable=True)  # JSON array: ["planner_change", "insight"]
    classification = Column(JSON, nullable=True)  # JSON: full orchestrator output
    proposed_actions = Column(JSON, nullable=True)  # JSON: what the agent wants to do
    approval_status = Column(String(50), nullable=True, default="not_required")  # pending | approved | rejected | not_required
    result = Column(JSON, nullable=True)  # JSON: final output
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ConversationSession(Base):
    """Conversationsession."""
    __tablename__ = "conversation_sessions"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    messages = relationship("ConversationMessage", back_populates="session", cascade="all, delete-orphan")

class ConversationMessage(Base):
    """Conversationmessage."""
    __tablename__ = "conversation_messages"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    conversation_id = Column(
        PortableUUID,
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_run_id = Column(
        PortableUUID,
        ForeignKey("workflow_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    role = Column(String(50), nullable=False)  # 'user' | 'assistant' | 'system'
    content = Column(JSON, nullable=False)  # JSON: {text, structured_type, structured_data}
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("ConversationSession", back_populates="messages")

class Memory(Base):
    """Memory."""
    __tablename__ = "memories"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        PortableUUID,
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    scope = Column(String(50), nullable=False)  # 'user_profile' | 'session' | 'episodic' | 'behavioral'
    category = Column(String(100), nullable=True)  # 'preference', 'pattern', 'constraint', etc.
    content = Column(Text, nullable=False)  # human-readable
    structured_value = Column(JSON, nullable=True)  # machine-readable
    source = Column(String(50), nullable=True)  # 'planner_action' | 'user_statement' | 'ai_inference'
    confidence = Column(Numeric(precision=3, scale=2), nullable=True, default=1.0)
    importance = Column(Numeric(precision=3, scale=2), nullable=True, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Integer, server_default="1", nullable=False) # boolean SQLite compat

class AuditEvent(Base):
    """Auditevent."""
    __tablename__ = "audit_events"

    id = Column(PortableUUID, primary_key=True, default=_uuid, index=True)
    user_id = Column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_run_id = Column(
        PortableUUID,
        ForeignKey("workflow_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(50), nullable=False)  # 'create_task' | 'delete_task' | 'move_task' | ...
    entity_type = Column(String(50), nullable=False)  # 'task' | 'template' | 'subtask'
    entity_id = Column(String(36), nullable=False, index=True)  # UUID of affected entity
    before_state = Column(JSON, nullable=True)  # JSON snapshot
    after_state = Column(JSON, nullable=True)  # JSON snapshot
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
