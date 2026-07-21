import logging
import re
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.jwt import create_access_token
from backend.core.security import hash_password, verify_password
from backend.db.models.core import User
from backend.schemas.auth_schema import UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user registration, authentication, and OAuth account linking."""

    def register(
        self, db: Session, email: str, password: str, timezone: str = "UTC"
    ) -> UserResponse:
        """Create a new user with email/password and timezone preference."""
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("User with this email already exists.")

        user = User(
            email=email,
            hashed_password=hash_password(password),
            timezone=timezone,
        )
        db.add(user)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("User already exists.")

        db.refresh(user)
        return UserResponse.model_validate(user)

    def login(self, db: Session, email: str, password: str) -> str | None:
        """Authenticate a user and return a JWT access token, or None if invalid."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.hashed_password:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return create_access_token({"sub": str(user.id), "email": user.email})

    def get_user_by_id(self, db: Session, user_id: UUID) -> User | None:
        """Look up a user by primary UUID key."""
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, db: Session, email: str) -> User | None:
        """Look up a user by email address."""
        return db.query(User).filter(User.email == email).first()

    def find_or_create_oauth_user(
        self,
        db: Session,
        email: str,
        provider: str,
        provider_id: str,
        username: str | None = None,
    ) -> User:
        """Find an existing user by OAuth provider ID, fall back to email, or create one.

        Strategy:
        1. Exact match on (auth_provider, auth_provider_id)  — same account, re-login.
        2. Match on email only — existing email/password user; link the OAuth provider.
        3. No match — create a brand-new OAuth-only user.
        """
        # 1. Lookup by provider identity (most specific)
        user = (
            db.query(User)
            .filter(
                User.auth_provider == provider,
                User.auth_provider_id == provider_id,
            )
            .first()
        )
        if user:
            return user

        # 2. Lookup by email (link provider to existing account)
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.auth_provider = provider          # type: ignore[assignment]
            user.auth_provider_id = provider_id    # type: ignore[assignment]
            db.commit()
            db.refresh(user)
            return user

        # 3. Create a new OAuth-only account (no password)
        user = User(
            email=email,
            hashed_password=None,
            auth_provider=provider,
            auth_provider_id=provider_id,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            # Race condition: another request created the user; try email lookup again
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                raise ValueError(f"Could not create OAuth user for email={email}")
            return user

        db.refresh(user)
        return user