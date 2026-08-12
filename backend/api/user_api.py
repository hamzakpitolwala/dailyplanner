from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.oauth2 import get_current_user
from backend.db.models.core import User
from backend.schemas.core_schema import UserProfileResponse, UserProfileUpdate
from backend.services.user_service import UserService
from backend.api.deps import get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    profile = await service.get_user_profile(user.id) # type: ignore
    return UserProfileResponse.model_validate(profile)


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_profile(
    data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    try:
        profile = await service.update_user_profile(user.id, data) # type: ignore
        return UserProfileResponse.model_validate(profile)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
