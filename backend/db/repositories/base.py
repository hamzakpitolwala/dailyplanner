from typing import Generic, TypeVar, Type, Sequence, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Generic repository implementation for SQLAlchemy models."""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> ModelType | None:
        result = await self.db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def list(self) -> Sequence[ModelType]:
        result = await self.db.execute(select(self.model))
        return result.scalars().all()

    async def create(self, db_obj: ModelType) -> ModelType:
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, **kwargs) -> ModelType:
        for field, value in kwargs.items():
            setattr(db_obj, field, value)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        await self.db.delete(db_obj)
        await self.db.commit()

    async def commit(self) -> None:
        await self.db.commit()

    async def refresh(self, db_obj: ModelType) -> None:
        await self.db.refresh(db_obj)
