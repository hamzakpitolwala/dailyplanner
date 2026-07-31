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
        """Instantiates all tasks in a template into concrete user tasks relative to start_date."""
        template = self.get_template(db, user_id, template_id)
        if not template:
            raise ValueError("Template not found")

        created_tasks = []
        for tmpl_task in template.template_tasks:
            calculated_start = start_date + timedelta(days=tmpl_task.relative_day_offset)
            calculated_due = calculated_start
            
            if tmpl_task.target_time:
                try:
                    # target_time is stored as a string "HH:MM:SS"
                    hour, minute, second = map(int, tmpl_task.target_time.split(":"))
                    calculated_start = calculated_start.replace(
                        hour=hour,
                        minute=minute,
                        second=second,
                    )
                    calculated_due = calculated_start + timedelta(minutes=tmpl_task.duration_minutes)
                except Exception:
                    pass

            task = Task(
                id=str(uuid.uuid4()),
                user_id=str(user_id),
                title=tmpl_task.title,
                description=tmpl_task.description,
                priority=tmpl_task.priority,
                checklist=tmpl_task.checklist,
                source_template_name=template.name,
                start_time=calculated_start,
                due_date=calculated_due,
            )
            db.add(task)
            db.flush()
            created_tasks.append(task)

        db.commit()
        return created_tasks

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