from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.jwt import decode_access_token
from backend.db.database import get_db
from backend.db.models.core import User
from backend.db.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.OAUTH2_TOKEN_URL)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the JWT and return the corresponding ``User``, or raise 401."""
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise _credentials_exception

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise _credentials_exception

    user_repo = UserRepository(db)
    user = None
    try:
        from uuid import UUID
        valid_uuid = UUID(user_id)
        user = await user_repo.get(valid_uuid)
    except ValueError:
        pass

    if not user:
        # Fallback: some older tokens may carry email in sub
        user = await user_repo.get_by_email(user_id)
    if not user:
        raise _credentials_exception

    return user
