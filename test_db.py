from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import declarative_base
from backend.core.config import settings
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class PortableUUID(TypeDecorator):
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=False))
        else:
            return dialect.type_descriptor(String(36))

Base = declarative_base()

class TestPortable(Base):
    __tablename__ = 'test_portable'
    id = Column(PortableUUID(), primary_key=True)

engine = create_engine(settings.DATABASE_URL)
try:
    Base.metadata.create_all(engine)
    print("Created PortableUUID table!")
except Exception as e:
    print("Error:", e)
