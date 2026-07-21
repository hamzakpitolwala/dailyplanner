"""pytest configuration: in-memory SQLite database for all tests.

Uses StaticPool so all connections and sessions in the test suite share the
exact same in-memory SQLite database. Enables foreign_keys PRAGMA for SQLite.
Normalizes UUID parameters in SQL queries to standard 36-char hyphenated string format
so String(36) model columns match regardless of whether SQLAlchemy dialect processed
them as 32-char hex or uuid.UUID objects.
Cleans DB tables between tests for complete test isolation.
"""

import os
import sqlite3
import uuid

# Automatically convert Python uuid.UUID objects to str for SQLite
sqlite3.register_adapter(uuid.UUID, lambda u: str(u))

# Must be set before any backend module is imported
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import all model modules so SQLAlchemy registers every table in metadata
import backend.db.models.core          # noqa: F401 — User, Category, Task
import backend.db.models.templates     # noqa: F401 — PlannerTemplate, TemplateTask
import backend.db.models.integrations  # noqa: F401 — UserOAuthToken, ExternalSyncedEvent
import backend.db.models.ai_engine     # noqa: F401 — AIUserProfile, AIRecommendation

from backend.db.database import Base, get_db
from backend.main import app

# ---------------------------------------------------------------------------
# In-memory SQLite engine with StaticPool
# ---------------------------------------------------------------------------

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _format_uuid_param(val):
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, str) and len(val) == 32:
        try:
            u = uuid.UUID(hex=val)
            return str(u)
        except ValueError:
            pass
    return val


@event.listens_for(_engine, "before_cursor_execute", retval=True)
def _convert_uuid_params(conn, cursor, statement, parameters, context, executemany):
    if isinstance(parameters, tuple):
        parameters = tuple(_format_uuid_param(p) for p in parameters)
    elif isinstance(parameters, list):
        parameters = [_format_uuid_param(p) for p in parameters]
    elif isinstance(parameters, dict):
        parameters = {k: _format_uuid_param(v) for k, v in parameters.items()}
    return statement, parameters


# Create all tables in the shared in-memory DB
Base.metadata.create_all(bind=_engine)

_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


# Wire dependency override
app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _clean_db():
    yield
    with _TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture
def db_session():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()
