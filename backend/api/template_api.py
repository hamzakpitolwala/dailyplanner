"""API routes for planner templates and template tasks."""

from datetime import datetime
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.oauth2 import get_current_user
from backend.db.database import get_db
from backend.db.models.core import User
from backend.db.models.templates import PlannerTemplate
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

router = APIRouter(prefix="/templates", tags=["templates"])
_service = TemplateService()


@router.get("", response_model=list[PlannerTemplateResponse])
async def list_templates(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[PlannerTemplateResponse]:
    return _service.list_templates(db, user.id) #type: ignore


@router.post("", response_model=PlannerTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: PlannerTemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlannerTemplateResponse:
    # NOTE: PlannerTemplateCreate now accepts an optional list of
    # template_tasks up front (nested creation), instead of the old
    # "in_use" flag, which no longer exists on the model.
    return _service.create_template(db, user.id, payload) #type: ignore


@router.get("/{template_id}", response_model=PlannerTemplateResponse)
async def get_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlannerTemplateResponse:
    template = _service.get_template(db, user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return template


@router.patch("/{template_id}", response_model=PlannerTemplateResponse)
async def update_template(
    template_id: UUID,
    payload: PlannerTemplateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlannerTemplateResponse:
    template = _service.get_template(db, user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return _service.update_template(db, template, payload)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    template = _service.get_template(db, user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    _service.delete_template(db, template)


# ------------------------------------------------------------------
# Template instantiation -> creates real Tasks from a template
# (replaces the old "apply in_use template" logic)
# ------------------------------------------------------------------


@router.post(
    "/{template_id}/apply",
    response_model=list[TaskResponse],
    status_code=status.HTTP_201_CREATED,
)
async def apply_template(
    template_id: UUID,
    target_date: datetime,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    """Instantiate all template_tasks in this template into real Tasks,
    anchored to target_date using each task's relative_day_offset/target_time."""
    try:
        return _service.instantiate_template_to_tasks(db, user.id, template_id, target_date) #type: ignore
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
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TemplateTaskResponse:
    template = _service.get_template(db, user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return _service.create_template_task(db, template, payload)


@router.patch("/{template_id}/tasks/{task_id}", response_model=TemplateTaskResponse)
async def update_template_task(
    template_id: UUID,
    task_id: UUID,
    payload: TemplateTaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TemplateTaskResponse:
    template = _service.get_template(db, user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    task = _service.get_template_task(db, template.id, task_id) #type: ignore
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template task not found"
        )

    return _service.update_template_task(db, task, payload)


@router.delete("/{template_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template_task(
    template_id: UUID,
    task_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    template = _service.get_template(db, user.id, template_id) #type: ignore
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    task = _service.get_template_task(db, template.id, task_id) #type: ignore
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template task not found"
        )

    _service.delete_template_task(db, task)