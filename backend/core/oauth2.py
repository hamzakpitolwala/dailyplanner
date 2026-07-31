from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.jwt import decode_access_token
from backend.db.database import get_db
from backend.db.models.core import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.OAUTH2_TOKEN_URL)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode the JWT and return the corresponding ``User``, or raise 401.

    The JWT payload produced by auth_services.login() looks like:
        {"sub": "<user-uuid-string>", "email": "user@example.com"}
    We look up the user by their UUID (sub) for correctness.
    """
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise _credentials_exception

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise _credentials_exception

    user = None
    try:
        from uuid import UUID
        # If it's a valid UUID, search by id
        valid_uuid = UUID(user_id)
        user = db.query(User).filter(User.id == valid_uuid).first()
    except ValueError:
        pass

    if not user:
        # Fallback: some older tokens may carry email in sub
        user = db.query(User).filter(User.email == user_id).first()
    if not user:
        raise _credentials_exception

    return user
