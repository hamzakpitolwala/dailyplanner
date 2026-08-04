from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from backend.db.models.core import Category, Task
from backend.schemas.core_schema import CategoryCreate, CategoryUpdate, TaskCreate, TaskUpdate


class TaskService:
    """Service layer for core Categories and Tasks."""

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    def list_categories(self, db: Session, user_id: UUID) -> list[Category]:
        return db.query(Category).filter(Category.user_id == user_id).all()

    def get_category(self, db: Session, user_id: UUID, category_id: UUID) -> Category | None:
        """Return a single category owned by user_id, or None if not found."""
        return (
            db.query(Category)
            .filter(Category.id == category_id, Category.user_id == user_id)
            .first()
        )

    def create_category(self, db: Session, user_id: UUID, data: CategoryCreate) -> Category:
        category = Category(user_id=str(user_id), **data.model_dump())
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    def update_category(
        self, db: Session, category: Category, data: CategoryUpdate
    ) -> Category:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        db.commit()
        db.refresh(category)
        return category

    def delete_category(self, db: Session, category: Category) -> None:
        db.delete(category)
        db.commit()

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def list_tasks(self, db: Session, user_id: UUID) -> list[Task]:
        from backend.db.models.core import TaskCheckin, ActivitySubtask
        return (
            db.query(Task)
            .options(
                selectinload(Task.category), 
                selectinload(Task.checkins).selectinload(TaskCheckin.missed_reason),
                selectinload(Task.checkins).selectinload(TaskCheckin.alternate_activity),
                selectinload(Task.subtasks)
            )
            .filter(Task.user_id == str(user_id))
            .order_by(Task.due_date.asc().nulls_last())
            .all()
        )

    def get_task(self, db: Session, user_id: UUID, task_id: UUID) -> Task | None:
        from backend.db.models.core import ActivitySubtask
        return (
            db.query(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.subtasks)
            )
            .filter(Task.id == str(task_id), Task.user_id == str(user_id))
            .first()
        )

    def create_task(self, db: Session, user_id: UUID, data: TaskCreate) -> Task:
        payload = data.model_dump(exclude={"subtasks"})
        if "category_id" in payload and payload["category_id"]:
            payload["category_id"] = str(payload["category_id"])
        
        # SQLite compat: convert bools to ints
        if "requires_reason" in payload and isinstance(payload["requires_reason"], bool):
            payload["requires_reason"] = 1 if payload["requires_reason"] else 0
        if "allows_alternate" in payload and isinstance(payload["allows_alternate"], bool):
            payload["allows_alternate"] = 1 if payload["allows_alternate"] else 0

        task = Task(user_id=str(user_id), **payload)
        db.add(task)
        db.flush()

        from backend.db.models.core import ActivitySubtask
        for sub_data in data.subtasks:
            sub_payload = sub_data.model_dump()
            if "is_completed" in sub_payload and isinstance(sub_payload["is_completed"], bool):
                sub_payload["is_completed"] = 1 if sub_payload["is_completed"] else 0
            subtask = ActivitySubtask(task_id=str(task.id), **sub_payload)
            db.add(subtask)

        db.commit()
        db.refresh(task)
        return task

    def update_task(self, db: Session, task: Task, data: TaskUpdate) -> Task:
        payload = data.model_dump(exclude_unset=True, exclude={"subtasks"})

        # Auto-set completed_at timestamp when status transitions to completed
        if payload.get("status") == "completed" and task.status != "completed": #type: ignore
            payload["completed_at"] = datetime.utcnow()

        # SQLite compat: convert bools to ints
        if "requires_reason" in payload and isinstance(payload["requires_reason"], bool):
            payload["requires_reason"] = 1 if payload["requires_reason"] else 0
        if "allows_alternate" in payload and isinstance(payload["allows_alternate"], bool):
            payload["allows_alternate"] = 1 if payload["allows_alternate"] else 0

        for field, value in payload.items():
            setattr(task, field, value)

        db.commit()
        db.refresh(task)
        return task

    def delete_task(self, db: Session, task: Task) -> None:
        db.delete(task)
        db.commit()

    # ------------------------------------------------------------------
    # Check-ins & Context
    # ------------------------------------------------------------------

    def list_pending_checkins(self, db: Session, user_id: UUID) -> list[Task]:
        from backend.db.models.core import TaskCheckin
        # Returns tasks that are auto-marked as 'not done' but have no check-in record yet
        return (
            db.query(Task)
            .filter(
                Task.user_id == str(user_id),
                Task.status.in_(["pending_not_done", "partial_not_done"]),
                (Task.requires_reason == 1) | (Task.allows_alternate == 1)
            )
            .outerjoin(TaskCheckin)
            .filter(TaskCheckin.id == None)
            .all()
        )

    def list_missed_reasons(self, db: Session, user_id: UUID) -> list:
        from backend.db.models.core import MissedReason
        return db.query(MissedReason).filter(
            (MissedReason.user_id == str(user_id)) | (MissedReason.user_id == None)
        ).all()

    def list_alternate_activities(self, db: Session, user_id: UUID) -> list:
        from backend.db.models.core import AlternateActivity
        return db.query(AlternateActivity).filter(
            (AlternateActivity.user_id == str(user_id)) | (AlternateActivity.user_id == None)
        ).all()

    def create_task_checkin(self, db: Session, task: Task, data: dict) -> object:
        from backend.db.models.core import TaskCheckin
        payload = data.copy()
        if "missed_reason_id" in payload and payload["missed_reason_id"]:
            payload["missed_reason_id"] = str(payload["missed_reason_id"])
        if "alternate_activity_id" in payload and payload["alternate_activity_id"]:
            payload["alternate_activity_id"] = str(payload["alternate_activity_id"])
        
        checkin = TaskCheckin(task_id=str(task.id), **payload)
        db.add(checkin)
        
        # Also update the task's status
        task.status = payload["status"]
        if task.status == "completed":
            task.completed_at = datetime.utcnow()
            
        db.commit()
        db.refresh(checkin)
        return checkin

    # ------------------------------------------------------------------
    # Subtasks
    # ------------------------------------------------------------------

    def get_subtask(self, db: Session, task_id: UUID, subtask_id: UUID) -> object | None:
        from backend.db.models.core import ActivitySubtask
        return (
            db.query(ActivitySubtask)
            .filter(ActivitySubtask.id == str(subtask_id), ActivitySubtask.task_id == str(task_id))
            .first()
        )

    def create_subtask(self, db: Session, task_id: UUID, data: dict) -> object:
        from backend.db.models.core import ActivitySubtask
        
        # SQLite compat: convert bools to ints
        payload = data.copy()
        if "is_completed" in payload and isinstance(payload["is_completed"], bool):
            payload["is_completed"] = 1 if payload["is_completed"] else 0

        subtask = ActivitySubtask(task_id=str(task_id), **payload)
        db.add(subtask)
        db.commit()
        db.refresh(subtask)
        return subtask

    def update_subtask(self, db: Session, subtask: object, data: dict) -> object:
        payload = data.copy()
        
        # SQLite compat: convert bools to ints
        if "is_completed" in payload and isinstance(payload["is_completed"], bool):
            payload["is_completed"] = 1 if payload["is_completed"] else 0

        for field, value in payload.items():
            setattr(subtask, field, value)

        db.commit()
        db.refresh(subtask)
        return subtask

    def delete_subtask(self, db: Session, subtask: object) -> None:
        db.delete(subtask)
        db.commit()