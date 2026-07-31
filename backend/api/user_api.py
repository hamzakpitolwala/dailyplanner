from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.core.oauth2 import get_current_user
from backend.db.database import get_db
from backend.db.models.core import User
from backend.schemas.core_schema import UserProfileResponse, UserProfileUpdate
from backend.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])
_service = UserService()


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    profile = _service.get_user_profile(db, user.id)
    return UserProfileResponse.model_validate(profile)


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_profile(
    data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = _service.update_user_profile(db, user.id, data)
    return UserProfileResponse.model_validate(profile)
