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
    """Decode the JWT and return the corresponding ``User``, or raise 401."""
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise _credentials_exception

    email: str | None = payload.get("sub")
    if not email:
        raise _credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise _credentials_exception

    return user
