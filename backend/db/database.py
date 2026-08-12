from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.core.config import settings
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class PortableUUID(TypeDecorator):
    """
    Portable UUID type for SQLAlchemy models.
    Maps to native UUID on PostgreSQL and String(36) on SQLite.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=False))
        else:
            return dialect.type_descriptor(String(36))

if not settings.DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Copy .env.example to .env and configure your database connection."
    )

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif db_url.startswith("sqlite://"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

if "?" in db_url:
    db_url = db_url.split("?")[0]

_connect_args: dict = {}
if db_url.startswith("postgresql+asyncpg"):
    _connect_args["ssl"] = "require"
    _connect_args["statement_cache_size"] = 0
    _connect_args["prepared_statement_cache_size"] = 0

_pool_kwargs: dict = {
    "pool_pre_ping": True,
}

if db_url.startswith("sqlite"):
    pass
else:
    # Neon Postgres aggressively closes idle SSL connections.
    # Keep the pool small and recycle connections frequently.
    _pool_kwargs.update(
        pool_size=5,
        max_overflow=5,
        pool_recycle=120,
        pool_timeout=30,
    )

engine = create_async_engine(
    db_url,
    connect_args=_connect_args,
    **_pool_kwargs,
)

SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    """Yield a database session and ensure it is closed after use."""
    async with SessionLocal() as db:
        yield db