from uuid import UUID
from sqlalchemy import select
from backend.db.models.core import FixedBlock
from backend.db.repositories.base import BaseRepository


class FixedBlockRepository(BaseRepository[FixedBlock]):
    """Repository handling FixedBlock operations."""

    def __init__(self, db):
        super().__init__(FixedBlock, db)

    async def list_fixed_blocks(self, user_id: UUID) -> list[FixedBlock]:
        result = await self.db.execute(
            select(FixedBlock).filter(FixedBlock.user_id == str(user_id))
        )
        return list(result.scalars().all())

    async def get_fixed_block(self, user_id: UUID, block_id: UUID) -> FixedBlock | None:
        result = await self.db.execute(
            select(FixedBlock).filter(
                FixedBlock.id == str(block_id), FixedBlock.user_id == str(user_id)
            )
        )
        return result.scalars().first()
