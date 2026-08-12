import uuid
from datetime import datetime, timezone, timedelta
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.security import hash_password
from backend.db.models.core import User
from backend.db.models.integrations import UserOAuthToken, ExternalSyncedEvent
from backend.schemas.integration_schema import (
    UserOAuthTokenResponse,
    ExternalSyncedEventCreate,
    ExternalSyncedEventResponse,
)
from backend.services.integration_service import IntegrationService


@pytest.fixture
def service(integration_service: IntegrationService) -> IntegrationService:
    return integration_service


@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_user(db_session: Session) -> User:
    unique_email = f"integ_user_{uuid.uuid4().hex[:8]}@example.com"
    user = User(email=unique_email, hashed_password=hash_password("secret1234"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_user(db_session: Session) -> User:
    unique_email = f"integ_user2_{uuid.uuid4().hex[:8]}@example.com"
    user = User(email=unique_email, hashed_password=hash_password("secret1234"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestOAuthTokens:
    @pytest.mark.asyncio
    async def test_get_oauth_tokens_success(self, db_session: Session, service: IntegrationService, test_user: User):
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        token_rec = UserOAuthToken(
            user_id=test_user.id,
            provider="google",
            access_token="acc-token-123",
            refresh_token="ref-token-456",
            scopes=["https://www.googleapis.com/auth/calendar.readonly"],
            expires_at=expires,
        )
        db_session.add(token_rec)
        await db_session.commit()

        token = await service.get_oauth_tokens(uuid.UUID(test_user.id), "google")
        assert token is not None
        assert token.access_token == "acc-token-123"
        assert token.provider == "google"

        # Validate with response schema
        validated = UserOAuthTokenResponse.model_validate(token)
        assert str(validated.user_id) == test_user.id
        assert validated.scopes == ["https://www.googleapis.com/auth/calendar.readonly"]

    @pytest.mark.asyncio
    async def test_get_oauth_tokens_not_found(self, service: IntegrationService, test_user: User):
        token = await service.get_oauth_tokens(uuid.UUID(test_user.id), "github")
        assert token is None

    @pytest.mark.asyncio
    async def test_get_oauth_tokens_user_isolation(
        self, db_session: Session, service: IntegrationService, test_user: User, other_user: User
    ):
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        token_rec = UserOAuthToken(
            user_id=test_user.id,
            provider="google",
            access_token="user1-token",
            refresh_token="user1-refresh",
            scopes=[],
            expires_at=expires,
        )
        db_session.add(token_rec)
        await db_session.commit()

        # Other user checks for google token
        token_other = await service.get_oauth_tokens(uuid.UUID(other_user.id), "google")
        assert token_other is None


class TestExternalSyncedEvents:
    @pytest.mark.asyncio
    async def test_sync_external_events_creates_new(self, service: IntegrationService, test_user: User):
        event_data = ExternalSyncedEventCreate(
            source_provider="google_calendar",
            external_id="evt_12345",
            event_type="calendar_event",
            parsed_summary="Team Sync Meeting",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            metadata={"location": "Zoom"},
        )

        synced = await service.sync_external_events(
            uuid.UUID(test_user.id), [event_data]
        )
        assert len(synced) == 1
        assert synced[0].external_id == "evt_12345"
        assert synced[0].parsed_summary == "Team Sync Meeting"
        assert synced[0].extra_metadata == {"location": "Zoom"}

        # Validate with response schema
        validated = ExternalSyncedEventResponse.model_validate(synced[0])
        assert str(validated.user_id) == test_user.id
        assert validated.external_id == "evt_12345"

    @pytest.mark.asyncio
    async def test_sync_external_events_upsert_existing(self, db_session: Session, service: IntegrationService, test_user: User):
        event_v1 = ExternalSyncedEventCreate(
            source_provider="google_calendar",
            external_id="evt_9999",
            event_type="calendar_event",
            parsed_summary="Original Title",
        )
        await service.sync_external_events(uuid.UUID(test_user.id), [event_v1])

        # Second sync with updated title
        event_v2 = ExternalSyncedEventCreate(
            source_provider="google_calendar",
            external_id="evt_9999",
            event_type="calendar_event",
            parsed_summary="Updated Title",
        )
        synced = await service.sync_external_events(uuid.UUID(test_user.id), [event_v2])

        assert len(synced) == 1
        assert synced[0].external_id == "evt_9999"
        assert synced[0].parsed_summary == "Updated Title"

        # Ensure no duplicate records created in DB
        total_records = len((
            await db_session.execute(
                select(ExternalSyncedEvent)
                .filter(
                    ExternalSyncedEvent.user_id == test_user.id,
                    ExternalSyncedEvent.external_id == "evt_9999",
                )
            )
        ).scalars().all())
        assert total_records == 1

    @pytest.mark.asyncio
    async def test_sync_external_events_user_isolation(
        self, service: IntegrationService, test_user: User, other_user: User
    ):
        event_user1 = ExternalSyncedEventCreate(
            source_provider="google_calendar",
            external_id="shared_external_id",
            event_type="meeting",
            parsed_summary="User 1 Event",
        )
        event_user2 = ExternalSyncedEventCreate(
            source_provider="google_calendar",
            external_id="shared_external_id",
            event_type="meeting",
            parsed_summary="User 2 Event",
        )

        synced1 = await service.sync_external_events(uuid.UUID(test_user.id), [event_user1])
        synced2 = await service.sync_external_events(uuid.UUID(other_user.id), [event_user2])

        assert synced1[0].user_id == test_user.id
        assert synced1[0].parsed_summary == "User 1 Event"

        assert synced2[0].user_id == other_user.id
        assert synced2[0].parsed_summary == "User 2 Event"
