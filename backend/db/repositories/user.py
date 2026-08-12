from uuid import UUID
from sqlalchemy import select
from backend.db.models.core import User, UserProfile
from backend.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository handling User operations."""

    def __init__(self, db):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def get_by_oauth_provider(self, provider: str, provider_id: str) -> User | None:
        result = await self.db.execute(
            select(User).filter(
                User.auth_provider == provider,
                User.auth_provider_id == provider_id,
            )
        )
        return result.scalars().first()


class UserProfileRepository(BaseRepository[UserProfile]):
    """Repository handling UserProfile operations."""

    def __init__(self, db):
        super().__init__(UserProfile, db)

    async def get_by_user_id(self, user_id: UUID) -> UserProfile | None:
        result = await self.db.execute(
            select(UserProfile).filter(UserProfile.user_id == str(user_id))
        )
        return result.scalars().first()

    async def get_by_username(self, username: str) -> UserProfile | None:
        result = await self.db.execute(
            select(UserProfile).filter(UserProfile.username == username)
        )
        return result.scalars().first()
