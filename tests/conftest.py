"""pytest configuration: in-memory SQLite database for all tests.

Uses StaticPool so all connections and sessions in the test suite share the
exact same in-memory SQLite database.
"""

import os
import sqlite3
import uuid
from pathlib import Path

# Automatically convert Python uuid.UUID objects to str for SQLite
sqlite3.register_adapter(uuid.UUID, lambda u: str(u))

# Must be set before any backend module is imported
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")
os.environ.setdefault("GOOGLE_CLIENT_ID", "")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "")
os.environ.setdefault("GITHUB_CLIENT_ID", "")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "")
os.environ.setdefault("TESTING", "1")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event, text
from sqlalchemy.pool import StaticPool

# Import all model modules so SQLAlchemy registers every table in metadata
import backend.db.models.core          # noqa: F401
import backend.db.models.templates     # noqa: F401
import backend.db.models.integrations  # noqa: F401
import backend.db.models.ai_engine     # noqa: F401

from backend.db.database import Base, get_db
from backend.main import app

# ---------------------------------------------------------------------------
# In-memory SQLite engine with StaticPool
# ---------------------------------------------------------------------------

_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_engine.sync_engine, "connect")
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


@event.listens_for(_engine.sync_engine, "before_cursor_execute", retval=True)
def _convert_uuid_params(conn, cursor, statement, parameters, context, executemany):
    if isinstance(parameters, tuple):
        parameters = tuple(_format_uuid_param(p) for p in parameters)
    elif isinstance(parameters, list):
        parameters = [_format_uuid_param(p) for p in parameters]
    elif isinstance(parameters, dict):
        parameters = {k: _format_uuid_param(v) for k, v in parameters.items()}
    return statement, parameters


_TestingSession = async_sessionmaker(autocommit=False, autoflush=False, bind=_engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_db():
    async with _TestingSession() as db:
        yield db


# Wire dependency override
app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(autouse=True)
async def _clean_db():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with _TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def db_session():
    async with _TestingSession() as db:
        yield db


@pytest.fixture
def auth_service(db_session):
    from backend.db.repositories.user import UserRepository
    from backend.services.auth_services import AuthService
    return AuthService(UserRepository(db_session))


@pytest.fixture
def user_service(db_session):
    from backend.db.repositories.user import UserProfileRepository
    from backend.db.repositories.task import CategoryRepository
    from backend.db.repositories.template import TemplateRepository, TemplateTaskRepository
    from backend.services.user_service import UserService
    return UserService(
        user_profile_repo=UserProfileRepository(db_session),
        category_repo=CategoryRepository(db_session),
        template_repo=TemplateRepository(db_session),
        template_task_repo=TemplateTaskRepository(db_session),
    )


@pytest.fixture
def task_service(db_session, integration_service):
    from backend.db.repositories.task import TaskRepository, CategoryRepository
    from backend.db.repositories.user import UserRepository
    from backend.services.task_service import TaskService
    return TaskService(
        task_repo=TaskRepository(db_session),
        category_repo=CategoryRepository(db_session),
        user_repo=UserRepository(db_session),
        integration_service=integration_service,
    )


@pytest.fixture
def template_service(db_session):
    from backend.db.repositories.template import TemplateRepository, TemplateTaskRepository
    from backend.db.repositories.task import TaskRepository
    from backend.services.template_service import TemplateService
    return TemplateService(
        template_repo=TemplateRepository(db_session),
        template_task_repo=TemplateTaskRepository(db_session),
        task_repo=TaskRepository(db_session),
    )


@pytest.fixture
def integration_service(db_session):
    from backend.db.repositories.integration import IntegrationRepository
    from backend.services.integration_service import IntegrationService
    return IntegrationService(IntegrationRepository(db_session))


@pytest.fixture
def ai_engine_service(db_session, task_service):
    from backend.db.repositories.ai_record import (
        AIUserProfileRepository, 
        AIRecommendationRepository,
        AISummaryRepository,
        RecommendationOutcomeRepository
    )
    from backend.services.llm_client import OllamaClient
    from backend.services.ai_engine_service import AIEngineService
    return AIEngineService(
        ai_profile_repo=AIUserProfileRepository(db_session),
        ai_recommendation_repo=AIRecommendationRepository(db_session),
        ai_summary_repo=AISummaryRepository(db_session),
        outcome_repo=RecommendationOutcomeRepository(db_session),
        llm_client=OllamaClient(),
        task_service=task_service,
    )
