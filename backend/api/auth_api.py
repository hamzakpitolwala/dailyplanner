"""API routes for authentication (register, login, token, current user)."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.requests import Request

from backend.core.oauth2 import get_current_user
from backend.db.models.core import User
from backend.schemas.auth_schema import TokenResponse, UserCreate, UserLogin, UserResponse, ChangePasswordRequest
from backend.services.auth_services import AuthService
from backend.core.limiter import limiter
from backend.api.deps import get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    try:
        result = await service.register(user.email, user.password, user.timezone)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return result


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    user: UserLogin,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    access_token = await service.login(user.email, user.password)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return TokenResponse(access_token=access_token)


@router.post("/token", response_model=TokenResponse)
@limiter.limit("10/minute")
async def token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    access_token = await service.login(form_data.username, form_data.password)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/change-password")
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    try:
        await service.change_password(user.id, data.old_password, data.new_password)
        return {"detail": "Password updated successfully"}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )