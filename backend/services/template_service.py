import uuid
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from backend.db.models.core import Task
from backend.db.models.templates import PlannerTemplate, TemplateTask
from backend.schemas.template_schema import (
    PlannerTemplateCreate,
    PlannerTemplateUpdate,
    TemplateTaskCreate,
    TemplateTaskUpdate,
)


class TemplateService:
    """Service layer for planner templates and template tasks."""

    # ------------------------------------------------------------------
    # Planner Templates
    # ------------------------------------------------------------------

    def list_templates(self, db: Session, user_id: UUID) -> list[PlannerTemplate]:
        return (
            db.query(PlannerTemplate)
            .options(selectinload(PlannerTemplate.template_tasks))
            .filter(PlannerTemplate.user_id == user_id)
            .order_by(PlannerTemplate.created_at.desc())
            .all()
        )

    def get_template(self, db: Session, user_id: UUID, template_id: UUID) -> PlannerTemplate | None:
        return (
            db.query(PlannerTemplate)
            .options(selectinload(PlannerTemplate.template_tasks))
            .filter(PlannerTemplate.id == template_id, PlannerTemplate.user_id == user_id)
            .first()
        )

    def create_template(
        self, db: Session, user_id: UUID, data: PlannerTemplateCreate
    ) -> PlannerTemplate:
        payload = data.model_dump(exclude={"template_tasks"})
        template = PlannerTemplate(user_id=str(user_id), **payload)
        db.add(template)
        db.flush()

        # Add initial nested template tasks if provided
        for task_data in data.template_tasks:
            tmpl_task = TemplateTask(template_id=str(template.id), **task_data.model_dump())
            db.add(tmpl_task)

        db.commit()
        db.refresh(template)
        return template

    def update_template(
        self, db: Session, template: PlannerTemplate, data: PlannerTemplateUpdate
    ) -> PlannerTemplate:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(template, field, value)

        db.commit()
        db.refresh(template)
        return template

    def delete_template(self, db: Session, template: PlannerTemplate) -> None:
        db.delete(template)
        db.commit()

    def instantiate_template_to_tasks(
        self, db: Session, user_id: UUID, template_id: UUID, start_date: datetime
    ) -> list[Task]:
        """Instantiates all tasks in a template into concrete user tasks relative to start_date.
        Acts as a sync: updates existing pending tasks, creates missing ones, and removes pending tasks that were deleted from the template."""
        template = self.get_template(db, user_id, template_id)
        if not template:
            raise ValueError("Template not found")

        # Clean up existing pending tasks from OTHER templates for this day
        start_of_day = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        other_template_tasks = db.query(Task).filter(
            Task.user_id == str(user_id),
            Task.source_template_name != None,
            Task.source_template_name != template.name,
            Task.due_date >= start_of_day,
            Task.due_date <= end_of_day,
            Task.status == "pending"
        ).all()
        
        for ot in other_template_tasks:
            db.delete(ot)

        # Get existing tasks for this date from this template, or manual tasks
        existing_tasks = db.query(Task).filter(
            Task.user_id == str(user_id),
            (Task.source_template_name == template.name) | (Task.source_template_name == None),
            Task.due_date >= start_of_day,
            Task.due_date <= end_of_day
        ).all()
        
        existing_by_tmpl_id = {}
        existing_by_title = {}
        for t in existing_tasks:
            if t.source_template_task_id:
                existing_by_tmpl_id.setdefault(t.source_template_task_id, []).append(t)
            else:
                existing_by_title.setdefault(t.title, []).append(t)
            
        synced_tasks = []

        for tmpl_task in template.template_tasks:
            calculated_start = start_date + timedelta(days=tmpl_task.relative_day_offset)
            calculated_due = calculated_start
            
            if tmpl_task.target_time:
                try:
                    import datetime
                    if isinstance(tmpl_task.target_time, datetime.time):
                        hour = tmpl_task.target_time.hour
                        minute = tmpl_task.target_time.minute
                        second = tmpl_task.target_time.second
                    else:
                        # target_time might be "HH:MM" or "HH:MM:SS"
                        parts = list(map(int, str(tmpl_task.target_time).split(":")))
                        hour, minute = parts[0], parts[1]
                        second = parts[2] if len(parts) > 2 else 0
                        
                    calculated_start = calculated_start.replace(
                        hour=hour,
                        minute=minute,
                        second=second,
                    )
                    calculated_due = calculated_start + timedelta(minutes=tmpl_task.duration_minutes)
                except Exception:
                    pass

            task = None
            if str(tmpl_task.id) in existing_by_tmpl_id and existing_by_tmpl_id[str(tmpl_task.id)]:
                task = existing_by_tmpl_id[str(tmpl_task.id)].pop(0)
            elif tmpl_task.title in existing_by_title and existing_by_title[tmpl_task.title]:
                # Fallback matching for old tasks
                task = existing_by_title[tmpl_task.title].pop(0)
                # Assign the missing id to fix the link
                task.source_template_task_id = str(tmpl_task.id)

            if task:
                if task.status == "pending":
                    # Overwrite core properties based on the template
                    task.title = tmpl_task.title
                    task.description = tmpl_task.description
                    task.priority = tmpl_task.priority
                    task.checklist = tmpl_task.checklist
                    
                    if tmpl_task.target_time is not None:
                        task.start_time = calculated_start
                        task.due_date = calculated_due
                    
                    # Sync subtasks non-destructively
                    from backend.db.models.core import ActivitySubtask
                    concrete_subs = {s.title: s for s in task.subtasks}
                    tmpl_sub_titles = set()
                    
                    for sub in tmpl_task.subtasks:
                        title = sub.get("title", "Unnamed")
                        tmpl_sub_titles.add(title)
                        if title not in concrete_subs:
                            # Create missing template subtask
                            new_sub = ActivitySubtask(
                                task_id=str(task.id),
                                title=title,
                                is_completed=1 if sub.get("is_completed") else 0,
                                is_template_subtask=1
                            )
                            db.add(new_sub)
                    
                    # Delete subtasks that were removed from the template,
                    # EXCEPT if they were manually added on the Planner Page (is_template_subtask == 0)
                    for s_title, subtask in concrete_subs.items():
                        if s_title not in tmpl_sub_titles and subtask.is_template_subtask == 1:
                            db.delete(subtask)
                        
                synced_tasks.append(task)
            else:
                task = Task(
                    id=str(uuid.uuid4()),
                    user_id=str(user_id),
                    title=tmpl_task.title,
                    description=tmpl_task.description,
                    priority=tmpl_task.priority,
                    checklist=tmpl_task.checklist,
                    source_template_name=template.name,
                    source_template_task_id=str(tmpl_task.id),
                    start_time=calculated_start,
                    due_date=calculated_due,
                )
                db.add(task)
                db.flush()
                
                from backend.db.models.core import ActivitySubtask
                for sub in tmpl_task.subtasks:
                    subtask = ActivitySubtask(
                        task_id=str(task.id),
                        title=sub.get("title", "Unnamed"),
                        is_completed=1 if sub.get("is_completed") else 0,
                        is_template_subtask=1
                    )
                    db.add(subtask)

                synced_tasks.append(task)

        # Remove tasks that are no longer in the template (only if pending)
        for task_list in existing_by_tmpl_id.values():
            for task in task_list:
                if task.status == "pending" and task.source_template_name == template.name:
                    db.delete(task)
        for task_list in existing_by_title.values():
            for task in task_list:
                if task.status == "pending" and task.source_template_name == template.name:
                    db.delete(task)

        db.commit()
        return synced_tasks

    # ------------------------------------------------------------------
    # Template Tasks
    # ------------------------------------------------------------------

    def create_template_task(
        self, db: Session, template: PlannerTemplate, data: TemplateTaskCreate
    ) -> TemplateTask:
        task = TemplateTask(template_id=str(template.id), **data.model_dump())
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def get_template_task(
        self, db: Session, template_id: UUID, task_id: UUID
    ) -> TemplateTask | None:
        return (
            db.query(TemplateTask)
            .filter(TemplateTask.id == task_id, TemplateTask.template_id == template_id)
            .first()
        )

    def update_template_task(
        self, db: Session, task: TemplateTask, data: TemplateTaskUpdate
    ) -> TemplateTask:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        db.commit()
        db.refresh(task)
        return task

    def delete_template_task(self, db: Session, task: TemplateTask) -> None:
        db.delete(task)
        db.commit()