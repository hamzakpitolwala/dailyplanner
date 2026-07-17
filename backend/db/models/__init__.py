"""Database models."""

# Import all models so SQLAlchemy discovers them for metadata.create_all()
from backend.db.models.user_table import User, UserSettings  # noqa: F401
from backend.db.models.planner_table import Activity, ActivityPolicy, DailyPlanner  # noqa: F401
from backend.db.models.history_table import ActivityHistoryEvent, AlternateActivity, MissedReason  # noqa: F401
from backend.db.models.template_table import PlannerTemplate, ActivityTemplate  # noqa: F401
