"""API routes for tasks and categories.

NOTE: This file has been rewritten around TaskService using request-based
Dependency Injection. There is no more direct database session passing or global
service instances.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.oauth2 import get_current_user
from backend.db.models.core import User
from backend.schemas.core_schema import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    MissedReasonResponse,
    AlternateActivityResponse,
    TaskCheckinCreate,
    TaskCheckinResponse,
    SubtaskCreate,
    SubtaskUpdate,
    SubtaskResponse,
)
from backend.services.task_service import TaskService
from backend.api.deps import get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])
categories_router = APIRouter(prefix="/categories", tags=["categories"])


# ------------------------------------------------------------------
# Tasks
# ------------------------------------------------------------------


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    target_date: str | None = None,
    tz_offset: int = 0,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    return await service.list_tasks(user.id, target_date, tz_offset, skip, limit) # type: ignore


@router.get("/earliest-date")
async def get_earliest_task_date(
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    date = await service.get_earliest_task_date(user.id)
    return {"earliest_date": date}


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    if payload.category_id is not None:
        category = await service.get_category(user.id, payload.category_id) # type: ignore
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )
    try:
        return await service.create_task(user.id, payload) # type: ignore
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("/missed-reasons", response_model=list[MissedReasonResponse])
async def list_missed_reasons(
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    return await service.list_missed_reasons(user.id) # type: ignore


@router.get("/missed-checkins", response_model=list[TaskResponse])
async def list_missed_checkins(
    tz_offset: int = 0,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    return await service.list_pending_checkins(user.id, tz_offset) # type: ignore


@router.get("/alternate-activities", response_model=list[AlternateActivityResponse])
async def list_alternate_activities(
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    return await service.list_alternate_activities(user.id) # type: ignore


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.get_task(user.id, task_id) # type: ignore
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/{task_id}/checkin", response_model=TaskCheckinResponse, status_code=status.HTTP_201_CREATED)
async def create_task_checkin(
    task_id: UUID,
    payload: TaskCheckinCreate,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    task = await service.get_task(user.id, task_id) # type: ignore
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return await service.create_task_checkin(task, payload)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.get_task(user.id, task_id) # type: ignore
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if payload.category_id is not None:
        category = await service.get_category(user.id, payload.category_id) # type: ignore
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )
    try:
        return await service.update_task(task, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    delete_in_calendar: bool = False,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> None:
    task = await service.get_task(user.id, task_id) # type: ignore
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    try:
        await service.delete_task(task, delete_in_calendar=delete_in_calendar)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ------------------------------------------------------------------
# Subtasks
# ------------------------------------------------------------------

@router.post("/{task_id}/subtasks", response_model=SubtaskResponse, status_code=status.HTTP_201_CREATED)
async def create_subtask(
    task_id: UUID,
    payload: SubtaskCreate,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    task = await service.get_task(user.id, task_id) # type: ignore
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return await service.create_subtask(task_id, payload)


@router.patch("/{task_id}/subtasks/{subtask_id}", response_model=SubtaskResponse)
async def update_subtask(
    task_id: UUID,
    subtask_id: UUID,
    payload: SubtaskUpdate,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    task = await service.get_task(user.id, task_id) # type: ignore
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    subtask = await service.get_subtask(task_id, subtask_id)
    if subtask is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subtask not found")
        
    return await service.update_subtask(subtask, payload)


@router.delete("/{task_id}/subtasks/{subtask_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subtask(
    task_id: UUID,
    subtask_id: UUID,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    task = await service.get_task(user.id, task_id) # type: ignore
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
    subtask = await service.get_subtask(task_id, subtask_id)
    if subtask is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subtask not found")
        
    await service.delete_subtask(subtask)


# ------------------------------------------------------------------
# Categories
# ------------------------------------------------------------------


@categories_router.get("", response_model=list[CategoryResponse])
async def list_categories(
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> list[CategoryResponse]:
    return await service.list_categories(user.id) # type: ignore


@categories_router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> CategoryResponse:
    return await service.create_category(user.id, payload) # type: ignore


@categories_router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> CategoryResponse:
    category = await service.get_category(user.id, category_id) # type: ignore
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return await service.update_category(category, payload)


@categories_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> None:
    category = await service.get_category(user.id, category_id) # type: ignore
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    await service.delete_category(category)