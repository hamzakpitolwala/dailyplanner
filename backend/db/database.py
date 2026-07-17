from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from backend.core.config import settings

if not settings.DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Copy .env.example to .env and configure your database connection."
    )

_connect_args: dict = {}
_pool_kwargs: dict = {
    "pool_pre_ping": True,
}

if settings.DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
else:
    # Neon Postgres aggressively closes idle SSL connections.
    # Keep the pool small and recycle connections frequently.
    _pool_kwargs.update(
        pool_size=5,
        max_overflow=5,
        pool_recycle=120,
        pool_timeout=30,
        poolclass=QueuePool,
    )

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    **_pool_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Yield a database session and ensure it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()