"""Database models.

Import all models here so SQLAlchemy discovers them for metadata.create_all()
"""

# Core domain models
from backend.db.models.core import Category, Task, User, UserProfile  # noqa: F401

# Template models
from backend.db.models.templates import PlannerTemplate, TemplateTask  # noqa: F401

# Integration / OAuth token models
from backend.db.models.integrations import ExternalSyncedEvent, UserOAuthToken  # noqa: F401

# AI engine models
from backend.db.models.ai_engine import AIRecommendation  # noqa: F401
from backend.db.models.agent import WorkflowRun, ConversationSession, ConversationMessage, Memory, AuditEvent  # noqa: F401
