from uuid import UUID
from sqlalchemy.orm import Session

from backend.db.models.integrations import ExternalSyncedEvent, UserOAuthToken
from backend.schemas.integration_schema import ExternalSyncedEventCreate


class IntegrationService:
    """Service layer for third-party OAuth integrations and external event syncing."""

    def get_oauth_tokens(self, db: Session, user_id: UUID, provider: str) -> UserOAuthToken | None:
        return (
            db.query(UserOAuthToken)
            .filter(UserOAuthToken.user_id == user_id, UserOAuthToken.provider == provider)
            .first()
        )

    def sync_external_events(
        self, db: Session, user_id: UUID, events: list[ExternalSyncedEventCreate]
    ) -> list[ExternalSyncedEvent]:
        synced_records = []
        for event_data in events:
            # Upsert logic based on user_id and external_id
            existing = (
                db.query(ExternalSyncedEvent)
                .filter(
                    ExternalSyncedEvent.user_id == user_id,
                    ExternalSyncedEvent.external_id == event_data.external_id,
                )
                .first()
            )

            if existing:
                for field, value in event_data.model_dump().items():
                    setattr(existing, field, value)
                synced_records.append(existing)
            else:
                new_event = ExternalSyncedEvent(user_id=user_id, **event_data.model_dump())
                db.add(new_event)
                synced_records.append(new_event)

        db.commit()
        return synced_records