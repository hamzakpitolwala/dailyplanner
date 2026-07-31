from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.core.oauth2 import get_current_user
from backend.db.models.core import User, FixedBlock
from backend.schemas.core_schema import FixedBlockCreate, FixedBlockUpdate, FixedBlockResponse

router = APIRouter(prefix="/fixed-blocks", tags=["fixed-blocks"])

@router.get("", response_model=list[FixedBlockResponse])
async def list_fixed_blocks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[FixedBlockResponse]:
    return db.query(FixedBlock).filter(FixedBlock.user_id == user.id).all()


@router.post("", response_model=FixedBlockResponse)
async def create_fixed_block(
    data: FixedBlockCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FixedBlockResponse:
    block = FixedBlock(
        user_id=user.id,
        name=data.name,
        start_time=data.start_time,
        end_time=data.end_time,
        days_of_week=data.days_of_week
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@router.put("/{block_id}", response_model=FixedBlockResponse)
async def update_fixed_block(
    block_id: UUID,
    data: FixedBlockUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FixedBlockResponse:
    block = db.query(FixedBlock).filter(FixedBlock.id == str(block_id), FixedBlock.user_id == user.id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Fixed block not found")
        
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(block, k, v)
        
    db.commit()
    db.refresh(block)
    return block


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fixed_block(
    block_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    block = db.query(FixedBlock).filter(FixedBlock.id == str(block_id), FixedBlock.user_id == user.id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Fixed block not found")
    
    db.delete(block)
    db.commit()
