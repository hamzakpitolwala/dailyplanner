import logging
import re

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.jwt import create_access_token
from backend.core.security import hash_password, verify_password
from backend.db.models.user_table import User, UserSettings
from backend.schemas.auth_schema import UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user registration, login, and lookup."""

    def register(
        self, db: Session, username: str, email: str, password: str
    ) -> UserResponse:
        """Create a new user and their default settings row.

        Raises ``ValueError`` if the email or username is already taken.
        """
        existing_user = (
            db.query(User)
            .filter((User.email == email) | (User.username == username))
            .first()
        )
        if existing_user:
            raise ValueError("User already exists")

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
        )
        db.add(user)

        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise ValueError("User already exists")

        settings = UserSettings(user_id=user.id)
        db.add(settings)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("User already exists")

        db.refresh(user)
        return UserResponse.model_validate(user)

    def login(self, db: Session, email: str, password: str) -> str | None:
        """Authenticate a user and return a JWT, or ``None`` on failure."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None

        if not user.hashed_password:
            # OAuth2-only account — cannot login with password
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return create_access_token({"sub": user.email})

    def get_user(self, db: Session, email: str) -> User | None:
        """Look up a user by email."""
        return db.query(User).filter(User.email == email).first()

    def find_or_create_oauth_user(
        self,
        db: Session,
        email: str,
        provider: str,
        provider_id: str,
        username: str,
    ) -> User:
        """Find an existing user by provider ID or email, or create a new one.

        Account linking: if a user registered with email/password and later
        signs in with an OAuth2 provider using the same email, the provider
        info is linked to the existing account.

        Raises ``ValueError`` on unrecoverable conflicts.
        """
        # 1. Check by provider + provider_id first (exact match)
        user = (
            db.query(User)
            .filter(User.auth_provider == provider, User.auth_provider_id == provider_id)
            .first()
        )
        if user:
            return user

        # 2. Check by email — link provider to existing account
        user = db.query(User).filter(User.email == email).first()
        if user:
            if not user.auth_provider:
                # Email/password user signing in via OAuth for the first time
                user.auth_provider = provider
                user.auth_provider_id = provider_id
                db.commit()
                db.refresh(user)
            return user

        # 3. Create a new user
        safe_username = self._unique_username(db, username)
        user = User(
            email=email,
            username=safe_username,
            hashed_password=None,
            auth_provider=provider,
            auth_provider_id=provider_id,
        )
        db.add(user)

        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise ValueError("Could not create OAuth2 user — email or username conflict")

        settings = UserSettings(user_id=user.id)
        db.add(settings)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Could not create OAuth2 user")

        db.refresh(user)
        return user

    @staticmethod
    def _unique_username(db: Session, name: str) -> str:
        """Derive a unique username from the provider's display name."""
        # Normalize: lowercase, keep only alphanumeric and underscores
        base = re.sub(r"[^a-z0-9_]", "", name.lower().replace(" ", "_"))
        if len(base) < 3:
            base = f"user_{base}"
        candidate = base
        suffix = 1
        while db.query(User).filter(User.username == candidate).first():
            candidate = f"{base}_{suffix}"
            suffix += 1
        return candidate