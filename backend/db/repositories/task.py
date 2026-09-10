from datetime import datetime, timezone, timedelta
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from backend.db.models.core import Task, Category, TaskCheckin, ActivitySubtask, MissedReason, AlternateActivity, User
from backend.db.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository handling Task and related sub-entities (Subtasks, Checkins)."""

    def __init__(self, db):
        """  init  ."""
        super().__init__(Task, db)

    async def list_tasks(
        self,
        user_id: UUID,
        target_date: str | None = None,
        tz_offset: int = 0,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """List tasks."""
        query = (
            select(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.checkins).selectinload(TaskCheckin.missed_reason),
                selectinload(Task.checkins).selectinload(TaskCheckin.alternate_activity),
                selectinload(Task.subtasks),
            )
            .filter(Task.user_id == str(user_id), Task.visibility != "hidden")
        )

        if target_date:
            tz = timezone(timedelta(minutes=-tz_offset))
            try:
                naive_start = datetime.strptime(target_date, "%Y-%m-%d")
                local_start = naive_start.replace(tzinfo=tz)
                start_of_day = local_start
                end_of_day = local_start.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
                query = query.filter(Task.due_date >= start_of_day, Task.due_date <= end_of_day)
            except ValueError:
                pass

        result = await self.db.execute(
            query.order_by(Task.due_date.asc().nulls_last()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_task_history(
        self,
        user_id: UUID,
        tz_offset: int = 0,
        skip: int = 0,
        limit: int = 1000,
    ) -> list[Task]:
        """Fetch past tasks ordered by date descending."""
        tz = timezone(timedelta(minutes=-tz_offset))
        now = datetime.now(tz)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        query = (
            select(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.checkins).selectinload(TaskCheckin.missed_reason),
                selectinload(Task.checkins).selectinload(TaskCheckin.alternate_activity),
                selectinload(Task.subtasks),
            )
            .filter(
                Task.user_id == str(user_id), 
                Task.visibility != "hidden",
                Task.due_date < start_of_today
            )
            .order_by(Task.due_date.desc().nulls_last())
        )
        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_task_status_counts(
        self, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> dict[str, int]:
        """Get task status counts."""
        query = (
            select(Task.status, func.count(Task.id))
            .filter(
                Task.user_id == str(user_id),
                Task.due_date >= start_date,
                Task.due_date <= end_date,
                Task.visibility != "hidden"
            )
            .group_by(Task.status)
        )
        result = await self.db.execute(query)
        return {status: count for status, count in result.all()}

    async def get_task_by_external_event(self, user_id: UUID, external_event_id: str) -> Task | None:
        """Get task by external event."""
        result = await self.db.execute(
            select(Task).filter(
                Task.user_id == str(user_id),
                Task.external_event_id == external_event_id,
            )
        )
        return result.scalars().first()

    async def get_tasks_by_external_events(self, user_id: UUID, external_event_ids: list[str]) -> list[Task]:
        """Get tasks by external events."""
        if not external_event_ids:
            return []
        result = await self.db.execute(
            select(Task).filter(
                Task.user_id == str(user_id),
                Task.external_event_id.in_(external_event_ids),
            )
        )
        return list(result.scalars().all())

    async def get_task(self, user_id: UUID, task_id: UUID) -> Task | None:
        """Get task."""
        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.subtasks),
                selectinload(Task.checkins).selectinload(TaskCheckin.missed_reason),
                selectinload(Task.checkins).selectinload(TaskCheckin.alternate_activity)
            )
            .filter(Task.id == str(task_id), Task.user_id == str(user_id))
        )
        return result.scalars().first()

    async def check_timing_conflict(
        self,
        user_id: UUID,
        start_time: datetime | None,
        due_date: datetime | None,
        exclude_task_id: str | None = None,
    ) -> Task | None:
        """Check timing conflict."""
        if not start_time or not due_date:
            return None

        query = select(Task).filter(
            Task.user_id == str(user_id),
            Task.start_time != None,
            Task.due_date != None,
            Task.start_time < due_date,
            Task.due_date > start_time,
        )
        if exclude_task_id:
            query = query.filter(Task.id != exclude_task_id)

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_earliest_task_date(self, user_id: UUID) -> str:
        # Get the earliest task date
        """Get earliest task date."""
        query = select(func.min(Task.due_date)).filter(Task.user_id == str(user_id))
        result = await self.db.execute(query)
        earliest_task_date = result.scalar()

        # Get the user's creation date
        user_query = select(User.created_at).filter(User.id == str(user_id))
        user_result = await self.db.execute(user_query)
        user_created_at = user_result.scalar()

        dates = []
        if earliest_task_date:
            dates.append(earliest_task_date)
        if user_created_at:
            dates.append(user_created_at)

        if dates:
            return min(dates).strftime("%Y-%m-%d")

        return datetime.now().strftime("%Y-%m-%d")

    async def get_past_pending_tasks(
        self, user_id: UUID, start_of_current_day: datetime
    ) -> list[Task]:
        """Get past pending tasks."""
        result = await self.db.execute(
            select(Task)
            .options(selectinload(Task.subtasks))
            .filter(
                Task.user_id == str(user_id),
                Task.status == "pending",
                Task.due_date < start_of_current_day,
            )
        )
        return list(result.scalars().all())

    async def list_pending_checkins(self, user_id: UUID) -> list[Task]:
        """List pending checkins."""
        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.checkins).selectinload(TaskCheckin.missed_reason),
                selectinload(Task.checkins).selectinload(TaskCheckin.alternate_activity),
                selectinload(Task.subtasks),
            )
            .filter(
                Task.user_id == str(user_id),
                Task.status.in_(["pending_not_done", "partial_not_done"]),
                (Task.requires_reason == 1) | (Task.allows_alternate == 1),
            )
            .outerjoin(TaskCheckin)
            .filter(TaskCheckin.id == None)
        )
        return list(result.scalars().all())

    async def list_missed_reasons(self, user_id: UUID) -> list[MissedReason]:
        """List missed reasons."""
        result = await self.db.execute(
            select(MissedReason).filter(
                (MissedReason.user_id == str(user_id)) | (MissedReason.user_id == None)
            )
        )
        return list(result.scalars().all())

    async def list_alternate_activities(self, user_id: UUID) -> list[AlternateActivity]:
        """List alternate activities."""
        result = await self.db.execute(
            select(AlternateActivity).filter(
                (AlternateActivity.user_id == str(user_id)) | (AlternateActivity.user_id == None)
            )
        )
        return list(result.scalars().all())

    # Subtask specific operations
    async def get_subtask(self, task_id: UUID, subtask_id: UUID) -> ActivitySubtask | None:
        """Get subtask."""
        result = await self.db.execute(
            select(ActivitySubtask).filter(
                ActivitySubtask.id == str(subtask_id),
                ActivitySubtask.task_id == str(task_id),
            )
        )
        return result.scalars().first()

    async def create_subtask(self, subtask: ActivitySubtask) -> ActivitySubtask:
        """Create subtask."""
        self.db.add(subtask)
        await self.db.commit()
        await self.db.refresh(subtask)
        return subtask

    async def delete_subtask(self, subtask: ActivitySubtask) -> None:
        """Delete subtask."""
        await self.db.delete(subtask)
        await self.db.commit()


class CategoryRepository(BaseRepository[Category]):
    """Repository handling Category operations."""

    def __init__(self, db):
        """  init  ."""
        super().__init__(Category, db)

    async def list_categories(self, user_id: UUID) -> list[Category]:
        """List categories."""
        result = await self.db.execute(select(Category).filter(Category.user_id == str(user_id)))
        return list(result.scalars().all())

    async def get_category(self, user_id: UUID, category_id: UUID) -> Category | None:
        """Get category."""
        result = await self.db.execute(
            select(Category).filter(
                Category.id == str(category_id), Category.user_id == str(user_id)
            )
        )
        return result.scalars().first()

    async def get_by_name(self, user_id: UUID, name: str) -> Category | None:
        """Get by name."""
        result = await self.db.execute(
            select(Category).filter(Category.user_id == str(user_id), Category.name == name)
        )
        return result.scalars().first()
