from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.core.oauth2 import get_current_user
from backend.db.database import get_db
from backend.db.models.user_table import User
from backend.schemas.auth_schema import TokenResponse, UserCreate, UserLogin, UserResponse
from backend.services.auth_services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
_service = AuthService()


@router.post("/register", response_model=UserResponse)
async def register(
    user: UserCreate, db: Session = Depends(get_db)
) -> UserResponse:
    try:
        result = _service.register(db, user.username, user.email, user.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return result


@router.post("/login", response_model=TokenResponse)
async def login(
    user: UserLogin, db: Session = Depends(get_db)
) -> TokenResponse:
    access_token = _service.login(db, user.email, user.password)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return TokenResponse(access_token=access_token)


@router.post("/token", response_model=TokenResponse)
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    access_token = _service.login(db, form_data.username, form_data.password)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)
