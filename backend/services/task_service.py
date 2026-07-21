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
        category = Category(user_id=user_id, **data.model_dump())
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
        return (
            db.query(Task)
            .options(selectinload(Task.category))
            .filter(Task.user_id == user_id)
            .order_by(Task.due_date.asc().nulls_last())
            .all()
        )

    def get_task(self, db: Session, user_id: UUID, task_id: UUID) -> Task | None:
        return (
            db.query(Task)
            .options(selectinload(Task.category))
            .filter(Task.id == task_id, Task.user_id == user_id)
            .first()
        )

    def create_task(self, db: Session, user_id: UUID, data: TaskCreate) -> Task:
        task = Task(user_id=user_id, **data.model_dump())
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def update_task(self, db: Session, task: Task, data: TaskUpdate) -> Task:
        payload = data.model_dump(exclude_unset=True)

        # Auto-set completed_at timestamp when status transitions to completed
        if payload.get("status") == "completed" and task.status != "completed": #type: ignore
            payload["completed_at"] = datetime.utcnow()

        for field, value in payload.items():
            setattr(task, field, value)

        db.commit()
        db.refresh(task)
        return task

    def delete_task(self, db: Session, task: Task) -> None:
        db.delete(task)
        db.commit()