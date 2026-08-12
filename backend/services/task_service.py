from datetime import datetime, timezone, timedelta
from uuid import UUID

from backend.db.models.core import Category, Task, TaskCheckin, ActivitySubtask
from backend.schemas.core_schema import (
    CategoryCreate,
    CategoryUpdate,
    TaskCreate,
    TaskUpdate,
    TaskCheckinCreate,
    SubtaskCreate,
    SubtaskUpdate,
)
from backend.db.repositories.task import TaskRepository, CategoryRepository
from backend.db.repositories.user import UserRepository


from backend.services.integration_service import IntegrationService
from backend.services.calendar_provider import CalendarProviderFactory
from backend.schemas.integration_schema import ExternalSyncedEventCreate


class TaskService:
    """Service layer for core Categories and Tasks."""

    def __init__(
        self,
        task_repo: TaskRepository,
        category_repo: CategoryRepository,
        user_repo: UserRepository,
        integration_service: IntegrationService | None = None,
    ):
        self.task_repo = task_repo
        self.category_repo = category_repo
        self.user_repo = user_repo
        self.integration_service = integration_service

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    async def list_categories(self, user_id: UUID) -> list[Category]:
        return await self.category_repo.list_categories(user_id)

    async def get_category(self, user_id: UUID, category_id: UUID) -> Category | None:
        """Return a single category owned by user_id, or None if not found."""
        return await self.category_repo.get_category(user_id, category_id)

    async def create_category(self, user_id: UUID, data: CategoryCreate) -> Category:
        category = Category(user_id=str(user_id), **data.model_dump())
        return await self.category_repo.create(category)

    async def update_category(
        self, category: Category, data: CategoryUpdate
    ) -> Category:
        return await self.category_repo.update(
            category, **data.model_dump(exclude_unset=True)
        )

    async def delete_category(self, category: Category) -> None:
        await self.category_repo.delete(category)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    async def _sync_calendar_events_for_day(
        self, user_id: UUID, target_date: str, tz_offset: int = 0
    ) -> None:
        """Import Google Calendar events for target_date into Task table (source='calendar')."""
        if not self.integration_service:
            return

        token_record = await self.integration_service.get_oauth_tokens(user_id, "google")
        if not token_record:
            return

        try:
            adapter = CalendarProviderFactory.get_provider("google")
            events = await adapter.fetch_events_for_day(token_record, target_date, tz_offset)

            if not events:
                return
                
            create_data_list = []
            for evt in events:
                create_data_list.append(
                    ExternalSyncedEventCreate(
                        source_provider="google",
                        external_id=evt["external_id"],
                        calendar_id=evt["calendar_id"],
                        event_type="calendar_event",
                        parsed_summary=evt["summary"],
                        summary=evt["summary"],
                        description=evt.get("description"),
                        location=evt.get("location"),
                        status=evt.get("status", "confirmed"),
                        start_time=evt.get("start_time"),
                        end_time=evt.get("end_time"),
                        raw_payload=evt.get("raw_payload"),
                    )
                )

            synced_list = await self.integration_service.sync_external_events(user_id, create_data_list)
            if not synced_list:
                return

            synced_event_ids = [str(evt.id) for evt in synced_list]
            existing_tasks = await self.task_repo.get_tasks_by_external_events(user_id, synced_event_ids)
            existing_tasks_map = {task.external_event_id: task for task in existing_tasks if task.external_event_id}

            synced_map = {evt.external_id: evt for evt in synced_list}

            for evt in events:
                synced_evt = synced_map.get(evt["external_id"])
                if not synced_evt:
                    continue

                existing_task = existing_tasks_map.get(str(synced_evt.id))

                if not existing_task:
                    new_task = Task(
                        user_id=str(user_id),
                        title=evt["summary"] or "Google Calendar Event",
                        description=evt.get("description"),
                        priority=1,
                        status="pending",
                        start_time=evt.get("start_time"),
                        due_date=evt.get("end_time") or evt.get("start_time"),
                        source="calendar",
                        external_event_id=str(synced_evt.id),
                        visibility="normal",
                    )
                    self.task_repo.db.add(new_task)
                else:
                    if existing_task.source == "calendar":
                        existing_task.title = evt["summary"] or existing_task.title
                        if evt.get("description"):
                            existing_task.description = evt["description"]
                        if evt.get("start_time"):
                            existing_task.start_time = evt["start_time"]
                        if evt.get("end_time"):
                            existing_task.due_date = evt["end_time"]

            await self.task_repo.db.flush()

            await self.task_repo.commit()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to auto-sync Google Calendar events for date %s: %s", target_date, exc)

    async def list_tasks(
        self,
        user_id: UUID,
        target_date: str | None = None,
        tz_offset: int = 0,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        return await self.task_repo.list_tasks(user_id, target_date, tz_offset, skip, limit)

    async def get_task_status_counts(
        self, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> dict[str, int]:
        return await self.task_repo.get_task_status_counts(user_id, start_date, end_date)

    async def sync_google_calendar_for_date(
        self, user_id: UUID, target_date: str, tz_offset: int = 0
    ) -> None:
        await self._sync_calendar_events_for_day(user_id, target_date, tz_offset)

    async def get_task(self, user_id: UUID, task_id: UUID) -> Task | None:
        return await self.task_repo.get_task(user_id, task_id)

    async def _check_timing_conflict(
        self,
        user_id: UUID,
        start_time: datetime | None,
        due_date: datetime | None,
        exclude_task_id: str | None = None,
    ) -> None:
        conflict = await self.task_repo.check_timing_conflict(
            user_id, start_time, due_date, exclude_task_id
        )
        if conflict:
            raise ValueError("Time slot is already occupied by another task.")

    async def create_task(self, user_id: UUID, data: TaskCreate) -> Task:
        payload = data.model_dump(exclude={"subtasks"})
        if "category_id" in payload and payload["category_id"]:
            payload["category_id"] = str(payload["category_id"])
        
        # SQLite compat: convert bools to ints
        if "requires_reason" in payload and isinstance(payload["requires_reason"], bool):
            payload["requires_reason"] = 1 if payload["requires_reason"] else 0
        if "allows_alternate" in payload and isinstance(payload["allows_alternate"], bool):
            payload["allows_alternate"] = 1 if payload["allows_alternate"] else 0

        start_time = payload.get("start_time")
        due_date = payload.get("due_date")
        await self._check_timing_conflict(user_id, start_time, due_date)

        # Handle calendar creation if source is calendar
        if payload.get("source") == "calendar" and self.integration_service:
            token_record = await self.integration_service.get_oauth_tokens(user_id, "google")
            if not token_record:
                raise ValueError("Google Calendar is not connected. Please connect it first in settings.")
            
            adapter = CalendarProviderFactory.get_provider("google")
            evt = await adapter.create_event(
                token_record=token_record,
                calendar_id="primary",
                summary=payload["title"],
                description=payload.get("description"),
                start_time=start_time,
                end_time=due_date,
            )
            
            create_data = ExternalSyncedEventCreate(
                source_provider="google",
                external_id=evt["id"],
                calendar_id="primary",
                event_type="calendar_event",
                parsed_summary=evt.get("summary", ""),
                summary=evt.get("summary"),
                description=evt.get("description"),
                location=evt.get("location"),
                status=evt.get("status", "confirmed"),
                start_time=start_time,
                end_time=due_date,
                raw_payload=evt,
            )
            synced_list = await self.integration_service.sync_external_events(user_id, [create_data])
            if synced_list:
                synced_evt = synced_list[0]
                payload["external_event_id"] = str(synced_evt.id)

        task = Task(user_id=str(user_id), **payload)
        self.task_repo.db.add(task)
        await self.task_repo.db.flush()

        for sub_data in data.subtasks:
            sub_payload = sub_data.model_dump()
            if "is_completed" in sub_payload and isinstance(sub_payload["is_completed"], bool):
                sub_payload["is_completed"] = 1 if sub_payload["is_completed"] else 0
            subtask = ActivitySubtask(task_id=str(task.id), **sub_payload)
            self.task_repo.db.add(subtask)

        await self.task_repo.commit()
        return await self.get_task(user_id, task.id)

    async def update_task(self, task: Task, data: TaskUpdate) -> Task:
        payload = data.model_dump(exclude_unset=True, exclude={"subtasks"})

        # Auto-set completed_at timestamp when status transitions to completed
        if payload.get("status") == "completed" and task.status != "completed": #type: ignore
            payload["completed_at"] = datetime.now(timezone.utc).replace(tzinfo=None)

        # SQLite compat: convert bools to ints
        if "requires_reason" in payload and isinstance(payload["requires_reason"], bool):
            payload["requires_reason"] = 1 if payload["requires_reason"] else 0
        if "allows_alternate" in payload and isinstance(payload["allows_alternate"], bool):
            payload["allows_alternate"] = 1 if payload["allows_alternate"] else 0

        new_start_time = payload.get("start_time", task.start_time)
        new_due_date = payload.get("due_date", task.due_date)
        
        if "start_time" in payload or "due_date" in payload:
            await self._check_timing_conflict(
                UUID(task.user_id),
                new_start_time,
                new_due_date,
                exclude_task_id=str(task.id),
            )

        # Handle external Google Calendar sync on task edit
        if task.source == "calendar" and task.external_event_id and self.integration_service:
            token_record = await self.integration_service.get_oauth_tokens(UUID(task.user_id), "google")
            if token_record and task.external_event:
                adapter = CalendarProviderFactory.get_provider("google")
                new_title = payload.get("title", task.title)
                new_desc = payload.get("description", task.description)
                # Attempt to update Google Calendar event
                await adapter.update_event(
                    token_record=token_record,
                    calendar_id=task.external_event.calendar_id or "primary",
                    external_id=task.external_event.external_id,
                    summary=new_title,
                    description=new_desc,
                    start_time=new_start_time,
                    end_time=new_due_date,
                )

        return await self.task_repo.update(task, **payload)

    async def get_earliest_task_date(self, user_id: UUID) -> str:
        return await self.task_repo.get_earliest_task_date(user_id)

    async def delete_task(self, task: Task, delete_in_calendar: bool = False) -> None:
        if task.source == "calendar" and task.external_event_id and self.integration_service:
            token_record = await self.integration_service.get_oauth_tokens(UUID(task.user_id), "google")
            if token_record and task.external_event:
                if delete_in_calendar:
                    adapter = CalendarProviderFactory.get_provider("google")
                    await adapter.cancel_event(
                        token_record=token_record,
                        calendar_id=task.external_event.calendar_id or "primary",
                        external_id=task.external_event.external_id,
                    )
                else:
                    # Remove from planner only -> set visibility to hidden
                    task.visibility = "hidden"
                    await self.task_repo.commit()
                    return

        await self.task_repo.delete(task)

    # ------------------------------------------------------------------
    # Check-ins & Context
    # ------------------------------------------------------------------

    async def list_pending_checkins(
        self, user_id: UUID, tz_offset: int = 0
    ) -> list[Task]:
        # Determine start of current day in user's timezone, converted to UTC
        tz = timezone(timedelta(minutes=-tz_offset))
        now = datetime.now(tz)
        start_of_current_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Sweep and transition any past tasks that are still "pending"
        past_pending = await self.task_repo.get_past_pending_tasks(
            user_id, start_of_current_day
        )
        for task in past_pending:
            has_completed_subtask = any(sub.is_completed for sub in task.subtasks)
            task.status = "partial_not_done" if has_completed_subtask else "pending_not_done"
        
        if past_pending:
            await self.task_repo.commit()

        # 2. Return tasks that are auto-marked as 'not done' but have no check-in record yet
        return await self.task_repo.list_pending_checkins(user_id)

    async def list_missed_reasons(self, user_id: UUID) -> list:
        return await self.task_repo.list_missed_reasons(user_id)

    async def list_alternate_activities(self, user_id: UUID) -> list:
        return await self.task_repo.list_alternate_activities(user_id)

    async def create_task_checkin(self, task: Task, data: TaskCheckinCreate) -> object:
        payload = data.model_dump(exclude_unset=True)
        if "missed_reason_id" in payload and payload["missed_reason_id"]:
            payload["missed_reason_id"] = str(payload["missed_reason_id"])
        if "alternate_activity_id" in payload and payload["alternate_activity_id"]:
            payload["alternate_activity_id"] = str(payload["alternate_activity_id"])
        
        checkin = TaskCheckin(task_id=str(task.id), **payload)
        self.task_repo.db.add(checkin)
        
        # Also update the task's status
        task.status = payload["status"]
        if task.status == "completed":
            task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
        await self.task_repo.commit()
        await self.task_repo.refresh(checkin)
        return checkin

    # ------------------------------------------------------------------
    # Subtasks
    # ------------------------------------------------------------------

    async def get_subtask(
        self, task_id: UUID, subtask_id: UUID
    ) -> ActivitySubtask | None:
        return await self.task_repo.get_subtask(task_id, subtask_id)

    async def create_subtask(self, task_id: UUID, data: SubtaskCreate) -> ActivitySubtask:
        # SQLite compat: convert bools to ints
        payload = data.model_dump(exclude_unset=True)
        if "is_completed" in payload and isinstance(payload["is_completed"], bool):
            payload["is_completed"] = 1 if payload["is_completed"] else 0

        subtask = ActivitySubtask(task_id=str(task_id), **payload)
        return await self.task_repo.create_subtask(subtask)

    async def update_subtask(
        self, subtask: ActivitySubtask, data: SubtaskUpdate
    ) -> ActivitySubtask:
        payload = data.model_dump(exclude_unset=True)
        
        # SQLite compat: convert bools to ints
        if "is_completed" in payload and isinstance(payload["is_completed"], bool):
            payload["is_completed"] = 1 if payload["is_completed"] else 0

        for field, value in payload.items():
            setattr(subtask, field, value)

        await self.task_repo.commit()
        await self.task_repo.refresh(subtask)
        return subtask

    async def delete_subtask(self, subtask: ActivitySubtask) -> None:
        await self.task_repo.delete_subtask(subtask)