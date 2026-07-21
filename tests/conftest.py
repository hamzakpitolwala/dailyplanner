"""pytest configuration: in-memory SQLite database for all tests.

The models use portable SQLAlchemy types (String/JSON) instead of
PostgreSQL-specific JSONB/ARRAY/UUID, so they work with SQLite out of the box.

The lifespan hook in main.py calls Base.metadata.create_all(bind=engine)
on startup — that's the production Postgres engine. We override get_db to
point at our in-memory SQLite engine, AND we manually call create_all on it
after importing all model modules so SQLAlchemy knows about every table.
"""

import os

# Must be set before any backend module is imported
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Import all model modules so SQLAlchemy registers every table in metadata
import backend.db.models.core          # noqa: F401 — User, Category, Task
import backend.db.models.templates     # noqa: F401 — PlannerTemplate, TemplateTask
import backend.db.models.integrations  # noqa: F401 — UserOAuthToken, ExternalSyncedEvent
import backend.db.models.ai_engine     # noqa: F401 — AIUserProfile, AIRecommendation

from backend.db.database import Base, get_db
from backend.main import app

# ---------------------------------------------------------------------------
# In-memory SQLite engine
# ---------------------------------------------------------------------------

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
)

# Use a single connection so the in-memory DB persists across multiple sessions
_connection = _engine.connect()

# Create all tables in the in-memory DB
Base.metadata.create_all(bind=_connection)

_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_connection)


def _override_get_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


# Wire dependency override
app.dependency_overrides[get_db] = _override_get_db
