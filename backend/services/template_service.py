import uuid
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.db.models.core import Task, ActivitySubtask, TaskCheckin
from backend.db.models.templates import PlannerTemplate, TemplateTask
from backend.schemas.template_schema import (
    PlannerTemplateCreate,
    PlannerTemplateUpdate,
    TemplateTaskCreate,
    TemplateTaskUpdate,
)
from backend.db.repositories.template import TemplateRepository, TemplateTaskRepository
from backend.db.repositories.task import TaskRepository


class TemplateService:
    """Service layer for planner templates and template tasks."""

    def __init__(
        self,
        template_repo: TemplateRepository,
        template_task_repo: TemplateTaskRepository,
        task_repo: TaskRepository,
    ):
        self.template_repo = template_repo
        self.template_task_repo = template_task_repo
        self.task_repo = task_repo

    # ------------------------------------------------------------------
    # Planner Templates
    # ------------------------------------------------------------------

    async def list_templates(self, user_id: UUID) -> list[PlannerTemplate]:
        return await self.template_repo.list_templates(user_id)

    async def get_template(self, user_id: UUID, template_id: UUID) -> PlannerTemplate | None:
        return await self.template_repo.get_template(user_id, template_id)

    async def get_template_by_name(self, user_id: UUID, name: str) -> PlannerTemplate | None:
        return await self.template_repo.get_template_by_name(user_id, name)

    async def create_template(
        self, user_id: UUID, data: PlannerTemplateCreate
    ) -> PlannerTemplate:
        payload = data.model_dump(exclude={"template_tasks"})
        template = PlannerTemplate(user_id=str(user_id), **payload)
        
        self.template_repo.db.add(template)
        await self.template_repo.db.flush()

        for task_data in data.template_tasks:
            tmpl_task = TemplateTask(template_id=str(template.id), **task_data.model_dump())
            self.template_repo.db.add(tmpl_task)

        await self.template_repo.commit()
        return await self.template_repo.get_template(user_id, template.id)

    async def update_template(
        self, template: PlannerTemplate, data: PlannerTemplateUpdate
    ) -> PlannerTemplate:
        return await self.template_repo.update(template, **data.model_dump(exclude_unset=True))

    async def delete_template(self, template: PlannerTemplate) -> None:
        await self.template_repo.delete(template)

    async def _clean_stale_tasks(
        self, user_id: UUID, template_id: UUID, start_of_day: datetime, end_of_day: datetime
    ) -> bool:
        stale_tasks = await self.template_repo.get_stale_template_tasks_to_clean(
            user_id, template_id, start_of_day, end_of_day
        )
        deleted_any = False
        for t in stale_tasks:
            await self.task_repo.db.delete(t)
            deleted_any = True
            
        if deleted_any:
            await self.task_repo.db.flush()
            
        return deleted_any

    def _parse_target_time(self, target_time: object) -> tuple[int, int, int]:
        from datetime import time as dt_time
        if isinstance(target_time, dt_time):
            return target_time.hour, target_time.minute, target_time.second
        parts = str(target_time).split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2]) if len(parts) > 2 else 0
        return hour, minute, second

    async def _sync_subtasks(self, task: Task, tmpl_task: TemplateTask) -> bool:
        concrete_subs = {s.title: s for s in task.subtasks}
        tmpl_sub_titles = set()
        
        changes_made = False
        for sub in tmpl_task.subtasks:
            title = sub.get("title", "Unnamed")
            tmpl_sub_titles.add(title)
            if title not in concrete_subs:
                new_sub = ActivitySubtask(
                    task_id=str(task.id),
                    title=title,
                    is_completed=1 if sub.get("is_completed") else 0,
                    is_template_subtask=1
                )
                self.template_repo.db.add(new_sub)
                changes_made = True
        
        for s_title, subtask in concrete_subs.items():
            if s_title not in tmpl_sub_titles and subtask.is_template_subtask == 1:
                self.template_repo.db.delete(subtask)
                changes_made = True
                
        return changes_made

    async def instantiate_template_to_tasks(
        self, user_id: UUID, template_id: UUID, start_date: datetime, tz_offset: int = 0
    ) -> list[Task]:
        """Instantiates all tasks in a template into concrete user tasks relative to start_date."""
        tz = timezone(timedelta(minutes=-tz_offset))
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=tz)
        else:
            start_date = start_date.astimezone(tz)
            
        template = await self.get_template(user_id, template_id)
        if not template:
            raise ValueError("Template not found")

        start_of_day = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        stale_cleaned = await self._clean_stale_tasks(user_id, template_id, start_of_day, end_of_day)
        
        result = await self.template_repo.db.execute(select(Task).options(
            selectinload(Task.subtasks),
            selectinload(Task.checkins).selectinload(TaskCheckin.missed_reason),
            selectinload(Task.checkins).selectinload(TaskCheckin.alternate_activity),
            selectinload(Task.category)
        ).filter(
            Task.user_id == str(user_id),
            (Task.source_template_id == str(template.id)) | (Task.source_template_id.is_(None)),
            Task.due_date >= start_of_day,
            Task.due_date <= end_of_day
        ))
        existing_tasks = result.scalars().all()
        
        existing_by_tmpl_id: dict[str, list] = {}
        existing_by_title: dict[str, list] = {}
        manual_tasks = []
        for t in existing_tasks:
            if t.source_template_task_id:
                existing_by_tmpl_id.setdefault(str(t.source_template_task_id), []).append(t)
            elif t.source_template_id:
                pass
            else:
                existing_by_title.setdefault(str(t.title), []).append(t)
                manual_tasks.append(t)
            
        synced_tasks = []
        changes_made = stale_cleaned

        for tmpl_task in template.template_tasks:
            target_day_start = start_of_day + timedelta(days=tmpl_task.relative_day_offset)
            target_day_end = end_of_day + timedelta(days=tmpl_task.relative_day_offset)
            
            if tmpl_task.target_time:
                hour, minute, second = self._parse_target_time(tmpl_task.target_time)
                calculated_start = target_day_start.replace(hour=hour, minute=minute, second=second)
                calculated_due = calculated_start + timedelta(minutes=tmpl_task.duration_minutes)
            else:
                calculated_start = None
                calculated_due = target_day_end
            
            # Check for conflict with manual tasks
            conflict = False
            if calculated_start and calculated_due:
                for mt in manual_tasks:
                    if mt.start_time and mt.due_date:
                        if calculated_start < mt.due_date and calculated_due > mt.start_time:
                            conflict = True
                            break
            if conflict:
                continue
            
            task = None
            if str(tmpl_task.id) in existing_by_tmpl_id and existing_by_tmpl_id[str(tmpl_task.id)]:
                task = existing_by_tmpl_id[str(tmpl_task.id)].pop(0)
            elif tmpl_task.title in existing_by_title and existing_by_title[tmpl_task.title]:
                task = existing_by_title[tmpl_task.title].pop(0)
                task.source_template_task_id = str(tmpl_task.id)
                task.source_template_id = str(template.id)
                changes_made = True

            if task:
                if task.status == "pending":
                    if (task.title != tmpl_task.title or 
                        task.description != tmpl_task.description or 
                        task.priority != tmpl_task.priority or 
                        task.checklist != tmpl_task.checklist or
                        task.requires_reason != (1 if tmpl_task.requires_reason else 0) or
                        task.allows_alternate != (1 if tmpl_task.allows_alternate else 0) or
                        task.source_template_name != template.name):
                        
                        task.title = tmpl_task.title
                        task.description = tmpl_task.description
                        task.priority = tmpl_task.priority
                        task.checklist = tmpl_task.checklist
                        task.source_template_name = template.name
                        task.requires_reason = 1 if tmpl_task.requires_reason else 0
                        task.allows_alternate = 1 if tmpl_task.allows_alternate else 0
                        changes_made = True
                    
                    if tmpl_task.target_time is not None:
                        if task.start_time != calculated_start:
                            task.start_time = calculated_start
                            changes_made = True
                        if task.due_date != calculated_due:
                            task.due_date = calculated_due
                            changes_made = True
                    
                    sub_changes = await self._sync_subtasks(task, tmpl_task)
                    if sub_changes:
                        changes_made = True
                        
                synced_tasks.append(task)
            else:
                task = Task(
                    id=str(uuid.uuid4()),
                    user_id=str(user_id),
                    title=tmpl_task.title,
                    description=tmpl_task.description,
                    priority=tmpl_task.priority,
                    checklist=tmpl_task.checklist,
                    source_template_id=str(template.id),
                    source_template_task_id=str(tmpl_task.id),
                    source_template_name=template.name,
                    start_time=calculated_start,
                    due_date=calculated_due,
                    requires_reason=int(tmpl_task.requires_reason) if tmpl_task.requires_reason else 0,
                    allows_alternate=int(tmpl_task.allows_alternate) if tmpl_task.allows_alternate else 0,
                )
                self.template_repo.db.add(task)
                await self.template_repo.db.flush()
                
                for sub in tmpl_task.subtasks:
                    subtask = ActivitySubtask(
                        task_id=str(task.id),
                        title=sub.get("title", "Unnamed"),
                        is_completed=1 if sub.get("is_completed") else 0,
                        is_template_subtask=1
                    )
                    self.template_repo.db.add(subtask)

                synced_tasks.append(task)
                changes_made = True

        if changes_made:
            await self.template_repo.commit()
            
        if not synced_tasks:
            return []
        
        if not changes_made:
            return synced_tasks
            
        task_ids = [str(t.id) for t in synced_tasks]
        result = await self.template_repo.db.execute(
            select(Task).options(
                selectinload(Task.subtasks), 
                selectinload(Task.category), 
                selectinload(Task.checkins)
            ).filter(Task.id.in_(task_ids)).execution_options(populate_existing=True)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Template Tasks
    # ------------------------------------------------------------------

    async def create_template_task(
        self, template: PlannerTemplate, data: TemplateTaskCreate
    ) -> TemplateTask:
        task = TemplateTask(template_id=str(template.id), **data.model_dump())
        return await self.template_task_repo.create(task)

    async def get_template_task(
        self, template_id: UUID, task_id: UUID
    ) -> TemplateTask | None:
        return await self.template_task_repo.get_template_task(template_id, task_id)

    async def update_template_task(
        self, task: TemplateTask, data: TemplateTaskUpdate
    ) -> TemplateTask:
        return await self.template_task_repo.update(task, **data.model_dump(exclude_unset=True))

    async def delete_template_task(self, task: TemplateTask) -> None:
        await self.template_task_repo.delete(task)