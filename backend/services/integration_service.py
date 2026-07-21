from uuid import UUID
from sqlalchemy.orm import Session

from backend.db.models.integrations import ExternalSyncedEvent, UserOAuthToken
from backend.schemas.integration_schema import ExternalSyncedEventCreate


class IntegrationService:
    """Service layer for third-party OAuth integrations and external event syncing."""

    def get_oauth_tokens(self, db: Session, user_id: UUID, provider: str) -> UserOAuthToken | None:
        user_id_str = str(user_id)
        return (
            db.query(UserOAuthToken)
            .filter(UserOAuthToken.user_id == user_id_str, UserOAuthToken.provider == provider)
            .first()
        )

    def sync_external_events(
        self, db: Session, user_id: UUID, events: list[ExternalSyncedEventCreate]
    ) -> list[ExternalSyncedEvent]:
        user_id_str = str(user_id)
        synced_records = []
        for event_data in events:
            dump = event_data.model_dump()
            if "metadata" in dump:
                dump["extra_metadata"] = dump.pop("metadata")

            # Upsert logic based on user_id and external_id
            existing = (
                db.query(ExternalSyncedEvent)
                .filter(
                    ExternalSyncedEvent.user_id == user_id_str,
                    ExternalSyncedEvent.external_id == event_data.external_id,
                )
                .first()
            )

            if existing:
                for field, value in dump.items():
                    setattr(existing, field, value)
                synced_records.append(existing)
            else:
                new_event = ExternalSyncedEvent(user_id=user_id_str, **dump)
                db.add(new_event)
                synced_records.append(new_event)

        db.commit()
        return synced_records