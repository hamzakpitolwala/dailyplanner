"""Shared test fixtures for the DailyPlanner test suite."""

import os
import sys

# Ensure the project root is on sys.path so ``backend.*`` imports resolve.
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Set minimal env vars *before* any application module is imported.
os.environ.setdefault("DATABASE_URL", "sqlite:///")
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")
os.environ.setdefault("GOOGLE_CLIENT_ID", "")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/auth/google/callback")
os.environ.setdefault("GITHUB_CLIENT_ID", "")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "")
os.environ.setdefault("GITHUB_REDIRECT_URI", "http://127.0.0.1:8000/auth/github/callback")

import pytest  # noqa: E402
from sqlalchemy import create_engine, StaticPool  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from backend.db.database import Base, get_db  # noqa: E402
from backend.main import app  # noqa: E402

# In-memory SQLite for full test isolation — each test session starts fresh.
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(autouse=True)
def _setup_db():
    """Create all tables before each test and tear them down after."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


def _override_get_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
