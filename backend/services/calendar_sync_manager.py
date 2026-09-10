import logging
from datetime import datetime
from uuid import UUID

from backend.db.models.core import Task
from backend.schemas.core_schema import TaskCreate, TaskUpdate
from backend.schemas.integration_schema import ExternalSyncedEventCreate
from backend.services.integration_service import IntegrationService
from backend.services.task_service import TaskService
from backend.services.calendar_provider import CalendarProviderFactory

logger = logging.getLogger(__name__)

class CalendarSyncManager:
    """Orchestrates 2-way sync between TaskService and Google Calendar."""

    def __init__(
        self,
        integration_service: IntegrationService,
        task_service: TaskService,
    ):
        """  init  ."""
        self.integration_service = integration_service
        self.task_service = task_service

    async def sync_google_calendar_for_date(
        self, user_id: UUID, target_date: str, tz_offset: int = 0
    ) -> None:
        """Import Google Calendar events for target_date into Task table."""
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
            existing_tasks = await self.task_service.task_repo.get_tasks_by_external_events(user_id, synced_event_ids)
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
                    self.task_service.task_repo.db.add(new_task)
                else:
                    if existing_task.source == "calendar":
                        existing_task.title = evt["summary"] or existing_task.title
                        if evt.get("description"):
                            existing_task.description = evt["description"]
                        if evt.get("start_time"):
                            existing_task.start_time = evt["start_time"]
                        if evt.get("end_time"):
                            existing_task.due_date = evt["end_time"]

            await self.task_service.task_repo.db.flush()
            await self.task_service.task_repo.commit()
        except Exception as exc:
            logger.warning("Failed to auto-sync Google Calendar events for date %s: %s", target_date, exc)

    async def create_task_with_sync(self, user_id: UUID, data: TaskCreate) -> Task:
        """Create a task and push to Google Calendar if source is 'calendar'."""
        if data.source == "calendar":
            token_record = await self.integration_service.get_oauth_tokens(user_id, "google")
            if not token_record:
                raise ValueError("Google Calendar is not connected. Please connect it first in settings.")
            
            adapter = CalendarProviderFactory.get_provider("google")
            evt = await adapter.create_event(
                token_record=token_record,
                calendar_id="primary",
                summary=data.title,
                description=data.description,
                start_time=data.start_time,
                end_time=data.due_date,
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
                start_time=data.start_time,
                end_time=data.due_date,
                raw_payload=evt,
            )
            synced_list = await self.integration_service.sync_external_events(user_id, [create_data])
            if synced_list:
                # We need to set the external_event_id on the task data before passing to TaskService
                data_dict = data.model_dump()
                data_dict["external_event_id"] = str(synced_list[0].id)
                data = TaskCreate(**data_dict)

        return await self.task_service.create_task(user_id, data)

    async def update_task_with_sync(self, task: Task, data: TaskUpdate) -> Task:
        """Update a task and push changes to Google Calendar if applicable."""
        payload = data.model_dump(exclude_unset=True)
        new_start_time = payload.get("start_time", task.start_time)
        new_due_date = payload.get("due_date", task.due_date)
        
        if task.source == "calendar" and task.external_event_id:
            token_record = await self.integration_service.get_oauth_tokens(UUID(task.user_id), "google")
            if token_record and task.external_event:
                adapter = CalendarProviderFactory.get_provider("google")
                new_title = payload.get("title", task.title)
                new_desc = payload.get("description", task.description)
                await adapter.update_event(
                    token_record=token_record,
                    calendar_id=task.external_event.calendar_id or "primary",
                    external_id=task.external_event.external_id,
                    summary=new_title,
                    description=new_desc,
                    start_time=new_start_time,
                    end_time=new_due_date,
                )

        return await self.task_service.update_task(task, data)

    async def delete_task_with_sync(self, task: Task, delete_in_calendar: bool = False) -> None:
        """Delete a task and optionally remove from Google Calendar."""
        if task.source == "calendar" and task.external_event_id:
            if not delete_in_calendar:
                task.visibility = "hidden"
                await self.task_service.task_repo.commit()
                return

            token_record = await self.integration_service.get_oauth_tokens(UUID(task.user_id), "google")
            if token_record and task.external_event:
                try:
                    adapter = CalendarProviderFactory.get_provider("google")
                    await adapter.cancel_event(
                        token_record=token_record,
                        calendar_id=task.external_event.calendar_id or "primary",
                        external_id=task.external_event.external_id,
                    )
                except Exception as e:
                    logger.warning("Failed to delete event in Google Calendar: %s", e)

        await self.task_service.delete_task(task)
