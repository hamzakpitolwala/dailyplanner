from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.db.models.templates import PlannerTemplate, TemplateTask
from backend.db.models.core import Task
from backend.db.repositories.base import BaseRepository


class TemplateRepository(BaseRepository[PlannerTemplate]):
    """Repository handling PlannerTemplate database operations."""

    def __init__(self, db):
        super().__init__(PlannerTemplate, db)

    async def list_templates(self, user_id: UUID) -> list[PlannerTemplate]:
        result = await self.db.execute(
            select(PlannerTemplate)
            .options(selectinload(PlannerTemplate.template_tasks))
            .filter(PlannerTemplate.user_id == str(user_id))
            .order_by(PlannerTemplate.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_template(self, user_id: UUID, template_id: UUID) -> PlannerTemplate | None:
        result = await self.db.execute(
            select(PlannerTemplate)
            .options(selectinload(PlannerTemplate.template_tasks))
            .filter(
                PlannerTemplate.id == str(template_id),
                PlannerTemplate.user_id == str(user_id),
            )
        )
        return result.scalars().first()

    async def get_stale_template_tasks_to_clean(
        self,
        user_id: UUID,
        template_id: UUID,
        start_of_day: datetime,
        end_of_day: datetime,
    ) -> list[Task]:
        cleanup_query = select(Task).filter(
            Task.user_id == str(user_id),
            Task.source_template_id != str(template_id),
            Task.source_template_id.isnot(None),
            Task.source_template_id != "",
            Task.status == "pending",
            Task.due_date >= start_of_day,
            Task.due_date <= end_of_day,
        )
        result = await self.db.execute(cleanup_query)
        return list(result.scalars().all())


class TemplateTaskRepository(BaseRepository[TemplateTask]):
    """Repository handling TemplateTask database operations."""

    def __init__(self, db):
        super().__init__(TemplateTask, db)

    async def get_template_task(
        self, template_id: UUID, template_task_id: UUID
    ) -> TemplateTask | None:
        result = await self.db.execute(
            select(TemplateTask).filter(
                TemplateTask.id == str(template_task_id),
                TemplateTask.template_id == str(template_id),
            )
        )
        return result.scalars().first()
