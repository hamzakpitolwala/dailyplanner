import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from backend.core.jwt import create_access_token
from backend.core.security import hash_password, verify_password
from backend.db.models.core import User
from backend.schemas.auth_schema import UserResponse
from backend.db.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user registration, authentication, and OAuth account linking."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(
        self, email: str, password: str, timezone: str = "UTC"
    ) -> UserResponse:
        """Create a new user with email/password and timezone preference."""
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists.")

        user = User(
            email=email,
            hashed_password=hash_password(password),
            timezone=timezone,
        )
        try:
            await self.user_repo.create(user)
        except IntegrityError:
            await self.user_repo.db.rollback()
            raise ValueError("User already exists.")

        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> str | None:
        """Authenticate a user and return a JWT access token, or None if invalid."""
        user = await self.user_repo.get_by_email(email)
        if not user or not user.hashed_password:
            return None

        if not verify_password(password, str(user.hashed_password)):
            return None

        return create_access_token({"sub": str(user.id), "email": user.email})

    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> None:
        """Change a user's password."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise ValueError("User not found.")
        
        if user.hashed_password and not verify_password(old_password, str(user.hashed_password)):
            raise ValueError("Incorrect old password.")
            
        await self.user_repo.update(user, hashed_password=hash_password(new_password))

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Look up a user by primary UUID key."""
        return await self.user_repo.get(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Look up a user by email address."""
        return await self.user_repo.get_by_email(email)

    async def find_or_create_oauth_user(
        self,
        email: str,
        provider: str,
        provider_id: str,
        username: str | None = None,
    ) -> User:
        # 1. Lookup by provider identity (most specific)
        user = await self.user_repo.get_by_oauth_provider(provider, provider_id)
        if user:
            return user

        # 2. Lookup by email (link provider to existing account)
        user = await self.user_repo.get_by_email(email)
        if user:
            await self.user_repo.update(
                user, auth_provider=provider, auth_provider_id=provider_id
            )
            return user

        # 3. Create a new OAuth-only account (no password)
        user = User(
            email=email,
            hashed_password=None,
            auth_provider=provider,
            auth_provider_id=provider_id,
        )
        try:
            await self.user_repo.create(user)
        except IntegrityError:
            await self.user_repo.db.rollback()
            # Race condition: another request created the user; try email lookup again
            user = await self.user_repo.get_by_email(email)
            if user is None:
                raise ValueError(f"Could not create OAuth user for email={email}")
            return user

        return user