from datetime import datetime
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value
from backend.db.models.templates import PlannerTemplate, TemplateTask
from backend.db.models.core import Task
from backend.db.repositories.base import BaseRepository


class TemplateRepository(BaseRepository[PlannerTemplate]):
    """Repository handling PlannerTemplate database operations."""

    def __init__(self, db):
        """  init  ."""
        super().__init__(PlannerTemplate, db)

    async def list_templates(self, user_id: UUID, active_id: str | None = None) -> list[PlannerTemplate]:
        """List templates."""
        query = (
            select(PlannerTemplate)
            .filter(PlannerTemplate.user_id == str(user_id))
            .order_by(PlannerTemplate.created_at.desc())
        )
        result = await self.db.execute(query)
        templates = list(result.scalars().all())

        if not templates:
            return []

        task_counts_query = (
            select(TemplateTask.template_id, func.count(TemplateTask.id))
            .filter(TemplateTask.template_id.in_([str(t.id) for t in templates]))
            .group_by(TemplateTask.template_id)
        )
        task_counts_result = await self.db.execute(task_counts_query)
        task_counts = dict(task_counts_result.all())

        for t in templates:
            set_committed_value(t, 'template_tasks', [])
            t.task_count = task_counts.get(str(t.id), 0)

        if active_id:
            active_tmpl = next((t for t in templates if str(t.id) == active_id), None)
            if active_tmpl:
                tasks_query = select(TemplateTask).filter(TemplateTask.template_id == active_id)
                tasks_result = await self.db.execute(tasks_query)
                set_committed_value(active_tmpl, 'template_tasks', list(tasks_result.scalars().all()))

        return templates

    async def get_template(self, user_id: UUID, template_id: UUID) -> PlannerTemplate | None:
        """Get template."""
        result = await self.db.execute(
            select(PlannerTemplate)
            .options(selectinload(PlannerTemplate.template_tasks))
            .filter(
                PlannerTemplate.id == str(template_id),
                PlannerTemplate.user_id == str(user_id),
            )
        )
        return result.scalars().first()

    async def get_template_by_name(self, user_id: UUID, name: str) -> PlannerTemplate | None:
        """Get template by name."""
        result = await self.db.execute(
            select(PlannerTemplate)
            .options(selectinload(PlannerTemplate.template_tasks))
            .filter(
                func.lower(PlannerTemplate.name) == func.lower(name),
                PlannerTemplate.user_id == str(user_id)
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
        """Get stale template tasks to clean."""
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
        """  init  ."""
        super().__init__(TemplateTask, db)

    async def get_template_task(
        self, template_id: UUID, template_task_id: UUID
    ) -> TemplateTask | None:
        """Get template task."""
        result = await self.db.execute(
            select(TemplateTask).filter(
                TemplateTask.id == str(template_task_id),
                TemplateTask.template_id == str(template_id),
            )
        )
        return result.scalars().first()
