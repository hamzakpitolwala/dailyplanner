"""API routes for planner templates and template tasks."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.oauth2 import get_current_user
from backend.db.models.core import User
from backend.schemas.core_schema import TaskResponse
from backend.schemas.template_schema import (
    PlannerTemplateCreate,
    PlannerTemplateResponse,
    PlannerTemplateUpdate,
    TemplateTaskCreate,
    TemplateTaskResponse,
    TemplateTaskUpdate,
)
from backend.services.template_service import TemplateService
from backend.api.deps import get_template_service

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[PlannerTemplateResponse])
async def list_templates(
    user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> list[PlannerTemplateResponse]:
    return await service.list_templates(user.id) #type: ignore


@router.post("", response_model=PlannerTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: PlannerTemplateCreate,
    user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> PlannerTemplateResponse:
    return await service.create_template(user.id, payload) #type: ignore


@router.get("/{template_id}", response_model=PlannerTemplateResponse)
async def get_template(
    template_id: UUID,
    user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> PlannerTemplateResponse:
    template = await service.get_template(user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return template


@router.patch("/{template_id}", response_model=PlannerTemplateResponse)
async def update_template(
    template_id: UUID,
    payload: PlannerTemplateUpdate,
    user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> PlannerTemplateResponse:
    template = await service.get_template(user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return await service.update_template(template, payload)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> None:
    template = await service.get_template(user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    await service.delete_template(template)


# ------------------------------------------------------------------
# Template instantiation -> creates real Tasks from a template
# ------------------------------------------------------------------


@router.post(
    "/{template_id}/apply",
    response_model=list[TaskResponse],
    status_code=status.HTTP_201_CREATED,
)
async def apply_template(
    template_id: UUID,
    target_date: datetime,
    tz_offset: int = 0,
    user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> list[TaskResponse]:
    """Instantiate all template_tasks in this template into real Tasks."""
    try:
        return await service.instantiate_template_to_tasks(user.id, template_id, target_date, tz_offset) #type: ignore
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


# ------------------------------------------------------------------
# Template Tasks (formerly "Activity Templates")
# ------------------------------------------------------------------


@router.post(
    "/{template_id}/tasks",
    response_model=TemplateTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template_task(
    template_id: UUID,
    payload: TemplateTaskCreate,
    user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> TemplateTaskResponse:
    template = await service.get_template(user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return await service.create_template_task(template, payload)


@router.patch("/{template_id}/tasks/{task_id}", response_model=TemplateTaskResponse)
async def update_template_task(
    template_id: UUID,
    task_id: UUID,
    payload: TemplateTaskUpdate,
    user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> TemplateTaskResponse:
    template = await service.get_template(user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    task = await service.get_template_task(template.id, task_id) #type: ignore
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template task not found"
        )
    return await service.update_template_task(task, payload)


@router.delete("/{template_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template_task(
    template_id: UUID,
    task_id: UUID,
    user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> None:
    template = await service.get_template(user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    task = await service.get_template_task(template.id, task_id) #type: ignore
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template task not found"
        )

    await service.delete_template_task(task)