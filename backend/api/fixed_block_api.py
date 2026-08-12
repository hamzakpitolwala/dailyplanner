from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.oauth2 import get_current_user
from backend.db.models.core import User, FixedBlock
from backend.schemas.core_schema import FixedBlockCreate, FixedBlockUpdate, FixedBlockResponse
from backend.db.repositories.fixed_block import FixedBlockRepository
from backend.api.deps import get_fixed_block_repository

router = APIRouter(prefix="/fixed-blocks", tags=["fixed-blocks"])


@router.get("", response_model=list[FixedBlockResponse])
async def list_fixed_blocks(
    user: User = Depends(get_current_user),
    repo: FixedBlockRepository = Depends(get_fixed_block_repository),
) -> list[FixedBlockResponse]:
    return await repo.list_fixed_blocks(user.id) # type: ignore


@router.post("", response_model=FixedBlockResponse)
async def create_fixed_block(
    data: FixedBlockCreate,
    user: User = Depends(get_current_user),
    repo: FixedBlockRepository = Depends(get_fixed_block_repository),
) -> FixedBlockResponse:
    block = FixedBlock(
        user_id=str(user.id), # type: ignore
        name=data.name,
        start_time=data.start_time,
        end_time=data.end_time,
        days_of_week=data.days_of_week
    )
    return await repo.create(block)


@router.put("/{block_id}", response_model=FixedBlockResponse)
async def update_fixed_block(
    block_id: UUID,
    data: FixedBlockUpdate,
    user: User = Depends(get_current_user),
    repo: FixedBlockRepository = Depends(get_fixed_block_repository),
) -> FixedBlockResponse:
    block = await repo.get_fixed_block(user.id, block_id) # type: ignore
    if not block:
        raise HTTPException(status_code=404, detail="Fixed block not found")
        
    update_data = data.model_dump(exclude_unset=True)
    return await repo.update(block, **update_data)


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fixed_block(
    block_id: UUID,
    user: User = Depends(get_current_user),
    repo: FixedBlockRepository = Depends(get_fixed_block_repository),
):
    block = await repo.get_fixed_block(user.id, block_id) # type: ignore
    if not block:
        raise HTTPException(status_code=404, detail="Fixed block not found")
    
    await repo.delete(block)
