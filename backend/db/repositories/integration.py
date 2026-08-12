from uuid import UUID
from sqlalchemy import select
from backend.db.models.integrations import UserOAuthToken, ExternalSyncedEvent
from backend.db.repositories.base import BaseRepository


class IntegrationRepository(BaseRepository[UserOAuthToken]):
    """Repository handling OAuth integration tokens and event syncs."""

    def __init__(self, db):
        super().__init__(UserOAuthToken, db)

    async def get_oauth_token(self, user_id: UUID, provider: str) -> UserOAuthToken | None:
        result = await self.db.execute(
            select(UserOAuthToken).filter(
                UserOAuthToken.user_id == str(user_id), UserOAuthToken.provider == provider
            )
        )
        return result.scalars().first()

    async def get_external_event(self, user_id: UUID, external_id: str) -> ExternalSyncedEvent | None:
        result = await self.db.execute(
            select(ExternalSyncedEvent).filter(
                ExternalSyncedEvent.user_id == str(user_id),
                ExternalSyncedEvent.external_id == external_id,
            )
        )
        return result.scalars().first()

    async def get_external_events(self, user_id: UUID, external_ids: list[str]) -> list[ExternalSyncedEvent]:
        if not external_ids:
            return []
        result = await self.db.execute(
            select(ExternalSyncedEvent).filter(
                ExternalSyncedEvent.user_id == str(user_id),
                ExternalSyncedEvent.external_id.in_(external_ids),
            )
        )
        return list(result.scalars().all())

    def add_external_event(self, event: ExternalSyncedEvent) -> None:
        self.db.add(event)

    async def upsert_oauth_token(
        self,
        user_id: UUID,
        provider: str,
        access_token: str,
        refresh_token: str,
        scopes: list[str],
        expires_at,
    ) -> UserOAuthToken:
        existing = await self.get_oauth_token(user_id, provider)
        if existing:
            existing.access_token = access_token
            if refresh_token:
                existing.refresh_token = refresh_token
            existing.scopes = scopes
            existing.expires_at = expires_at
            token = existing
        else:
            token = UserOAuthToken(
                user_id=str(user_id),
                provider=provider,
                access_token=access_token,
                refresh_token=refresh_token or "",
                scopes=scopes,
                expires_at=expires_at,
            )
            self.db.add(token)
        await self.commit()
        await self.refresh(token)
        return token

    async def delete_oauth_token(self, user_id: UUID, provider: str) -> bool:
        existing = await self.get_oauth_token(user_id, provider)
        if existing:
            await self.db.delete(existing)
            await self.commit()
            return True
        return False

