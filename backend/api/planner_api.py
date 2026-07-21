# """API routes for tasks and categories.

# NOTE: This file used to expose DailyPlanner + Activity endpoints.
# Those models no longer exist in the refactored schema — they were
# replaced by a single flat `Task` table (with a JSONB checklist) and a
# separate `Category` table. This file has been rewritten around
# TaskService accordingly. There is no more "daily planner wrapper" or
# `/planners/today` concept; due_date on Task now carries that role.
# """

# from uuid import UUID

# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session

# from backend.core.oauth2 import get_current_user
# from backend.db.database import get_db
# from backend.db.models.core import User
# from backend.schemas.core_schema import (
#     CategoryCreate,
#     CategoryResponse,
#     CategoryUpdate,
#     TaskCreate,
#     TaskResponse,
#     TaskUpdate,
# )
# from backend.services.task_service import TaskService

# router = APIRouter(prefix="/tasks", tags=["tasks"])
# categories_router = APIRouter(prefix="/categories", tags=["categories"])
# _service = TaskService()


# # ------------------------------------------------------------------
# # Tasks
# # ------------------------------------------------------------------


# @router.get("", response_model=list[TaskResponse])
# async def list_tasks(
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user),
# ) -> list[TaskResponse]:
#     return _service.list_tasks(db, user.id) #type: ignore


# @router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
# async def create_task(
#     payload: TaskCreate,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user),
# ) -> TaskResponse:
#     return _service.create_task(db, user.id, payload) #type: ignore


# @router.get("/{task_id}", response_model=TaskResponse)
# async def get_task(
#     task_id: UUID,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user),
# ) -> TaskResponse:
#     task = _service.get_task(db, user.id, task_id) #type: ignore
#     if task is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
#     return task


# @router.patch("/{task_id}", response_model=TaskResponse)
# async def update_task(
#     task_id: UUID,
#     payload: TaskUpdate,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user),
# ) -> TaskResponse:
#     task = _service.get_task(db, user.id, task_id) #type: ignore
#     if task is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
#     return _service.update_task(db, task, payload)


# @router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_task(
#     task_id: UUID,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user),
# ) -> None:
#     task = _service.get_task(db, user.id, task_id) #type: ignore
#     if task is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
#     _service.delete_task(db, task)


# # ------------------------------------------------------------------
# # Categories
# # ------------------------------------------------------------------


# @categories_router.get("", response_model=list[CategoryResponse])
# async def list_categories(
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user),
# ) -> list[CategoryResponse]:
#     return _service.list_categories(db, user.id) #type: ignore


# @categories_router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
# async def create_category(
#     payload: CategoryCreate,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user),
# ) -> CategoryResponse:
#     return _service.create_category(db, user.id, payload) #type: ignore


# @categories_router.patch("/{category_id}", response_model=CategoryResponse)
# async def update_category(
#     category_id: UUID,
#     payload: CategoryUpdate,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user),
# ) -> CategoryResponse:
#     categories = _service.list_categories(db, user.id) #type: ignore
#     category = next((c for c in categories if c.id == category_id), None) #type: ignore
#     if category is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
#     return _service.update_category(db, category, payload)


# @categories_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_category(
#     category_id: UUID,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user),
# ) -> None:
#     categories = _service.list_categories(db, user.id) #type: ignore
#     category = next((c for c in categories if c.id == category_id), None) #type: ignore
#     if category is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
#     _service.delete_category(db, category)

"""API routes for tasks and categories.

NOTE: This file used to expose DailyPlanner + Activity endpoints.
Those models no longer exist in the refactored schema — they were
replaced by a single flat `Task` table (with a JSONB checklist) and a
separate `Category` table. This file has been rewritten around
TaskService accordingly. There is no more "daily planner wrapper" or
`/planners/today` concept; due_date on Task now carries that role.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.oauth2 import get_current_user
from backend.db.database import get_db
from backend.db.models.core import User
from backend.schemas.core_schema import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from backend.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])
categories_router = APIRouter(prefix="/categories", tags=["categories"])
_service = TaskService()


# ------------------------------------------------------------------
# Tasks
# ------------------------------------------------------------------


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    return _service.list_tasks(db, user.id)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskResponse:
    if payload.category_id is not None:
        category = _service.get_category(db, user.id, payload.category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )
    return _service.create_task(db, user.id, payload)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskResponse:
    task = _service.get_task(db, user.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskResponse:
    task = _service.get_task(db, user.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if payload.category_id is not None:
        category = _service.get_category(db, user.id, payload.category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )
    return _service.update_task(db, task, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    task = _service.get_task(db, user.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _service.delete_task(db, task)


# ------------------------------------------------------------------
# Categories
# ------------------------------------------------------------------


@categories_router.get("", response_model=list[CategoryResponse])
async def list_categories(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CategoryResponse]:
    return _service.list_categories(db, user.id)


@categories_router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CategoryResponse:
    return _service.create_category(db, user.id, payload)


@categories_router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CategoryResponse:
    category = _service.get_category(db, user.id, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return _service.update_category(db, category, payload)


@categories_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    category = _service.get_category(db, user.id, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    _service.delete_category(db, category)