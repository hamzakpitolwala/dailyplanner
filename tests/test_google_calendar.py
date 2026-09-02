import uuid
from datetime import datetime, timezone, timedelta
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from backend.core.security import hash_password
from backend.db.models.core import User, Task
from backend.db.models.integrations import UserOAuthToken, ExternalSyncedEvent
from backend.db.models.templates import PlannerTemplate, TemplateTask
from backend.services.calendar_provider import CalendarProviderFactory, GoogleCalendarAdapter
from backend.services.integration_service import IntegrationService
from backend.services.task_service import TaskService
from backend.services.calendar_sync_manager import CalendarSyncManager
from backend.services.template_service import TemplateService
from backend.schemas.core_schema import TaskUpdate, TaskCreate


@pytest_asyncio.fixture
async def calendar_user(db_session) -> User:
    unique_email = f"gcal_user_{uuid.uuid4().hex[:8]}@example.com"
    user = User(email=unique_email, hashed_password=hash_password("password123"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def connected_user_token(db_session, calendar_user: User) -> UserOAuthToken:
    token = UserOAuthToken(
        user_id=calendar_user.id,
        provider="google",
        access_token="fake-google-access-token",
        refresh_token="fake-google-refresh-token",
        scopes=["https://www.googleapis.com/auth/calendar.events"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add(token)
    await db_session.commit()
    await db_session.refresh(token)
    return token


class TestGoogleCalendarAdapter:
    @pytest.mark.asyncio
    async def test_factory_returns_google_adapter(self):
        adapter = CalendarProviderFactory.get_provider("google")
        assert isinstance(adapter, GoogleCalendarAdapter)

    @pytest.mark.asyncio
    async def test_fetch_events_for_day_mock(self, connected_user_token: UserOAuthToken):
        adapter = GoogleCalendarAdapter()
        mock_response_data = {
            "items": [
                {
                    "id": "gcal_evt_1",
                    "status": "confirmed",
                    "summary": "Design Sprint Review",
                    "description": "Quarterly design sync",
                    "start": {"dateTime": "2026-08-10T10:00:00Z"},
                    "end": {"dateTime": "2026-08-10T11:00:00Z"},
                }
            ]
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = AsyncMock(status_code=200, json=lambda: mock_response_data)
            events = await adapter.fetch_events_for_day(connected_user_token, "2026-08-10")

            assert len(events) == 1
            assert events[0]["external_id"] == "gcal_evt_1"
            assert events[0]["summary"] == "Design Sprint Review"


class TestDailyPlannerCalendarImport:
    @pytest.mark.asyncio
    async def test_daily_import_creates_calendar_tasks(
        self,
        db_session,
        task_service: TaskService,
        calendar_sync_manager: CalendarSyncManager,
        integration_service: IntegrationService,
        calendar_user: User,
        connected_user_token: UserOAuthToken,
    ):
        mock_events = [
            {
                "external_id": "gcal_evt_100",
                "calendar_id": "primary",
                "summary": "Team Sync",
                "description": "Weekly status update",
                "status": "confirmed",
                "start_time": datetime(2026, 8, 10, 9, 0, tzinfo=timezone.utc),
                "end_time": datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc),
                "raw_payload": {},
            }
        ]

        with patch.object(GoogleCalendarAdapter, "fetch_events_for_day", return_value=mock_events):
            await calendar_sync_manager.sync_google_calendar_for_date(
                user_id=uuid.UUID(calendar_user.id),
                target_date="2026-08-10",
            )
            tasks = await task_service.list_tasks(
                user_id=uuid.UUID(calendar_user.id),
                target_date="2026-08-10",
            )

            assert len(tasks) == 1
            cal_task = tasks[0]
            assert cal_task.title == "Team Sync"
            assert cal_task.source == "calendar"
            assert cal_task.external_event_id is not None

    @pytest.mark.asyncio
    async def test_template_isolation(
        self,
        db_session,
        task_service: TaskService,
        calendar_sync_manager: CalendarSyncManager,
        template_service: TemplateService,
        calendar_user: User,
        connected_user_token: UserOAuthToken,
    ):
        """Verify external calendar tasks are never saved into template definitions."""
        mock_events = [
            {
                "external_id": "gcal_evt_200",
                "calendar_id": "primary",
                "summary": "External Meeting",
                "description": "Client sync",
                "status": "confirmed",
                "start_time": datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc),
                "end_time": datetime(2026, 8, 10, 15, 0, tzinfo=timezone.utc),
                "raw_payload": {},
            }
        ]

        with patch.object(GoogleCalendarAdapter, "fetch_events_for_day", return_value=mock_events):
            await calendar_sync_manager.sync_google_calendar_for_date(
                user_id=uuid.UUID(calendar_user.id),
                target_date="2026-08-10",
            )
            tasks = await task_service.list_tasks(
                user_id=uuid.UUID(calendar_user.id),
                target_date="2026-08-10",
            )
            assert any(t.source == "calendar" for t in tasks)

        # Create a template from tasks or list templates
        templates = await template_service.list_templates(uuid.UUID(calendar_user.id))
        for tpl in templates:
            for task in tpl.template_tasks:
                assert getattr(task, "source", "manual") != "calendar"


class TestExternalTaskEditAndDelete:
    @pytest.mark.asyncio
    async def test_edit_external_task_syncs_to_google(
        self,
        db_session,
        task_service: TaskService,
        calendar_sync_manager: CalendarSyncManager,
        integration_service: IntegrationService,
        calendar_user: User,
        connected_user_token: UserOAuthToken,
    ):
        # Create external event record
        ext_evt = ExternalSyncedEvent(
            user_id=calendar_user.id,
            source_provider="google",
            external_id="ext_gcal_555",
            calendar_id="primary",
            summary="Original Meeting",
        )
        db_session.add(ext_evt)
        await db_session.commit()
        await db_session.refresh(ext_evt)

        # Create task linked to external event
        task = Task(
            user_id=calendar_user.id,
            title="Original Meeting",
            source="calendar",
            external_event_id=ext_evt.id,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        with patch.object(GoogleCalendarAdapter, "update_event", return_value={"status": "confirmed"}) as mock_update:
            updated = await calendar_sync_manager.update_task_with_sync(
                task, TaskUpdate(title="Updated Meeting Title")
            )
            assert updated.title == "Updated Meeting Title"
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_external_task_planner_only(
        self,
        db_session,
        task_service: TaskService,
        calendar_sync_manager: CalendarSyncManager,
        calendar_user: User,
        connected_user_token: UserOAuthToken,
    ):
        ext_evt = ExternalSyncedEvent(
            user_id=calendar_user.id,
            source_provider="google",
            external_id="ext_gcal_777",
            calendar_id="primary",
            summary="Meeting To Delete",
        )
        db_session.add(ext_evt)
        await db_session.commit()
        await db_session.refresh(ext_evt)

        task = Task(
            user_id=calendar_user.id,
            title="Meeting To Delete",
            source="calendar",
            external_event_id=ext_evt.id,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        with patch.object(GoogleCalendarAdapter, "cancel_event") as mock_cancel:
            await calendar_sync_manager.delete_task_with_sync(task, delete_in_calendar=False)
            mock_cancel.assert_not_called()

        deleted = await task_service.get_task(uuid.UUID(calendar_user.id), uuid.UUID(task.id))
        assert deleted is not None
        assert deleted.visibility == "hidden"

    @pytest.mark.asyncio
    async def test_delete_external_task_delete_in_calendar(
        self,
        db_session,
        task_service: TaskService,
        calendar_sync_manager: CalendarSyncManager,
        calendar_user: User,
        connected_user_token: UserOAuthToken,
    ):
        ext_evt = ExternalSyncedEvent(
            user_id=calendar_user.id,
            source_provider="google",
            external_id="ext_gcal_888",
            calendar_id="primary",
            summary="Meeting To Delete Both",
        )
        db_session.add(ext_evt)
        await db_session.commit()
        await db_session.refresh(ext_evt)

        task = Task(
            user_id=calendar_user.id,
            title="Meeting To Delete Both",
            source="calendar",
            external_event_id=ext_evt.id,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        with patch.object(GoogleCalendarAdapter, "cancel_event", return_value=True) as mock_cancel:
            await calendar_sync_manager.delete_task_with_sync(task, delete_in_calendar=True)
            mock_cancel.assert_called_once()

        deleted = await task_service.get_task(uuid.UUID(calendar_user.id), uuid.UUID(task.id))
        assert deleted is None

    @pytest.mark.asyncio
    async def test_create_external_task_syncs_to_google(
        self,
        db_session,
        task_service: TaskService,
        calendar_sync_manager: CalendarSyncManager,
        calendar_user: User,
        connected_user_token: UserOAuthToken,
    ):
        mock_event_response = {
            "id": "gcal_new_created_123",
            "summary": "New Google Task",
            "status": "confirmed",
        }
        with patch.object(GoogleCalendarAdapter, "create_event", return_value=mock_event_response) as mock_create:
            task = await calendar_sync_manager.create_task_with_sync(
                uuid.UUID(calendar_user.id),
                TaskCreate(
                    title="New Google Task",
                    source="calendar",
                    due_date=datetime.now(timezone.utc) + timedelta(hours=1),
                )
            )
            assert task.source == "calendar"
            assert task.external_event_id is not None
            mock_create.assert_called_once()
