from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

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



class TaskService:
    """Service layer for core Categories and Tasks."""

    def __init__(
        self,
        task_repo: TaskRepository,
        category_repo: CategoryRepository,
        user_repo: UserRepository,
    ):
        """  init  ."""
        self.task_repo = task_repo
        self.category_repo = category_repo
        self.user_repo = user_repo

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    async def list_categories(self, user_id: UUID) -> list[Category]:
        """List categories."""
        return await self.category_repo.list_categories(user_id)

    async def get_category(self, user_id: UUID, category_id: UUID) -> Category | None:
        """Return a single category owned by user_id, or None if not found."""
        return await self.category_repo.get_category(user_id, category_id)

    async def create_category(self, user_id: UUID, data: CategoryCreate) -> Category:
        """Create category."""
        category = Category(user_id=str(user_id), **data.model_dump())
        return await self.category_repo.create(category)

    async def update_category(
        self, category: Category, data: CategoryUpdate
    ) -> Category:
        """Update category."""
        return await self.category_repo.update(
            category, **data.model_dump(exclude_unset=True)
        )

    async def delete_category(self, category: Category) -> None:
        """Delete category."""
        await self.category_repo.delete(category)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------



    async def list_tasks(
        self,
        user_id: UUID,
        target_date: str | None = None,
        tz_offset: int = 0,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """List tasks."""
        return await self.task_repo.list_tasks(user_id, target_date, tz_offset, skip, limit)

    async def list_task_history(
        self,
        user_id: UUID,
        tz_offset: int = 0,
        skip: int = 0,
        limit: int = 1000,
    ) -> list[Task]:
        """List task history."""
        return await self.task_repo.get_task_history(user_id, tz_offset, skip, limit)

    async def get_task_status_counts(
        self, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> dict[str, int]:
        """Get task status counts."""
        return await self.task_repo.get_task_status_counts(user_id, start_date, end_date)



    async def get_task(self, user_id: UUID, task_id: UUID) -> Task | None:
        """Get task."""
        return await self.task_repo.get_task(user_id, task_id)

    async def _check_timing_conflict(
        self,
        user_id: UUID,
        start_time: datetime | None,
        due_date: datetime | None,
        exclude_task_id: str | None = None,
    ) -> None:
        """ check timing conflict."""
        conflict = await self.task_repo.check_timing_conflict(
            user_id, start_time, due_date, exclude_task_id
        )
        if conflict:
            raise ValueError("Time slot is already occupied by another task.")

    async def create_task(self, user_id: UUID, data: TaskCreate) -> Task:
        """Create task."""
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
        """Update task."""
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



        return await self.task_repo.update(task, **payload)

    async def get_earliest_task_date(self, user_id: UUID) -> str:
        """Get earliest task date."""
        return await self.task_repo.get_earliest_task_date(user_id)

    async def delete_task(self, task: Task) -> None:
        """Delete task."""
        await self.task_repo.delete(task)

    # ------------------------------------------------------------------
    # Check-ins & Context
    # ------------------------------------------------------------------

    async def list_pending_checkins(
        self, user_id: UUID, tz_offset: int = 0
    ) -> list[Task]:
        # Determine start of current day in user's timezone, converted to UTC
        """List pending checkins."""
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
        """List missed reasons."""
        return await self.task_repo.list_missed_reasons(user_id)

    async def list_alternate_activities(self, user_id: UUID) -> list:
        """List alternate activities."""
        return await self.task_repo.list_alternate_activities(user_id)

    async def create_task_checkin(self, task: Task, data: TaskCheckinCreate) -> object:
        """Create task checkin."""
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
            
        await self.task_repo.db.flush()
        checkin_id = str(checkin.id)
        
        await self.task_repo.commit()
        
        # Reload the checkin with relationships to satisfy TaskCheckinResponse schema
        stmt = select(TaskCheckin).options(
            selectinload(TaskCheckin.missed_reason),
            selectinload(TaskCheckin.alternate_activity)
        ).filter(TaskCheckin.id == checkin_id).execution_options(populate_existing=True)
        
        result = await self.task_repo.db.execute(stmt)
        return result.scalars().first()

    # ------------------------------------------------------------------
    # Subtasks
    # ------------------------------------------------------------------

    async def get_subtask(
        self, task_id: UUID, subtask_id: UUID
    ) -> ActivitySubtask | None:
        """Get subtask."""
        return await self.task_repo.get_subtask(task_id, subtask_id)

    async def create_subtask(self, task_id: UUID, data: SubtaskCreate) -> ActivitySubtask:
        # SQLite compat: convert bools to ints
        """Create subtask."""
        payload = data.model_dump(exclude_unset=True)
        if "is_completed" in payload and isinstance(payload["is_completed"], bool):
            payload["is_completed"] = 1 if payload["is_completed"] else 0

        subtask = ActivitySubtask(task_id=str(task_id), **payload)
        return await self.task_repo.create_subtask(subtask)

    async def update_subtask(
        self, subtask: ActivitySubtask, data: SubtaskUpdate
    ) -> ActivitySubtask:
        """Update subtask."""
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
        """Delete subtask."""
        await self.task_repo.delete_subtask(subtask)
