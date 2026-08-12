from uuid import UUID

from backend.db.models.integrations import ExternalSyncedEvent, UserOAuthToken
from backend.schemas.integration_schema import ExternalSyncedEventCreate
from backend.db.repositories.integration import IntegrationRepository


class IntegrationService:
    """Service layer for third-party OAuth integrations and external event syncing."""

    def __init__(self, integration_repo: IntegrationRepository):
        self.integration_repo = integration_repo

    async def get_oauth_tokens(self, user_id: UUID, provider: str) -> UserOAuthToken | None:
        return await self.integration_repo.get_oauth_token(user_id, provider)

    async def save_oauth_tokens(
        self,
        user_id: UUID,
        provider: str,
        access_token: str,
        refresh_token: str,
        scopes: list[str],
        expires_at,
    ) -> UserOAuthToken:
        return await self.integration_repo.upsert_oauth_token(
            user_id, provider, access_token, refresh_token, scopes, expires_at
        )

    async def disconnect_provider(self, user_id: UUID, provider: str) -> bool:
        return await self.integration_repo.delete_oauth_token(user_id, provider)

    async def sync_external_events(
        self, user_id: UUID, events: list[ExternalSyncedEventCreate]
    ) -> list[ExternalSyncedEvent]:
        if not events:
            return []

        synced_records = []
        external_ids = [e.external_id for e in events]
        existing_events = await self.integration_repo.get_external_events(user_id, external_ids)
        existing_map = {e.external_id: e for e in existing_events}

        for event_data in events:
            dump = event_data.model_dump()
            if "metadata" in dump:
                dump["extra_metadata"] = dump.pop("metadata")

            existing = existing_map.get(event_data.external_id)

            if existing:
                for field, value in dump.items():
                    setattr(existing, field, value)
                synced_records.append(existing)
            else:
                new_event = ExternalSyncedEvent(user_id=str(user_id), **dump)
                self.integration_repo.add_external_event(new_event)
                synced_records.append(new_event)

        await self.integration_repo.commit()
        return synced_records