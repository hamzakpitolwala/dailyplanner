"""API routes for planner templates."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.oauth2 import get_current_user
from backend.db.database import get_db
from backend.db.models.user_table import User
from backend.schemas.template_schema import (
    PlannerTemplateCreate,
    PlannerTemplateResponse,
    PlannerTemplateUpdate,
    ActivityTemplateCreate,
    ActivityTemplateResponse,
    ActivityTemplateUpdate,
)
from backend.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])
_service = TemplateService()


@router.get("", response_model=list[PlannerTemplateResponse])
async def list_templates(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[PlannerTemplateResponse]:
    return _service.list_templates(db, user.id)


@router.post("", response_model=PlannerTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: PlannerTemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlannerTemplateResponse:
    return _service.create_template(db, user.id, payload)


@router.get("/{template_id}", response_model=PlannerTemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlannerTemplateResponse:
    template = _service.get_template(db, user.id, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return template


@router.patch("/{template_id}", response_model=PlannerTemplateResponse)
async def update_template(
    template_id: int,
    payload: PlannerTemplateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlannerTemplateResponse:
    template = _service.get_template(db, user.id, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return _service.update_template(db, user.id, template, payload)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    template = _service.get_template(db, user.id, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    _service.delete_template(db, template)


# ------------------------------------------------------------------
# Activity Templates
# ------------------------------------------------------------------


@router.post("/{template_id}/activities", response_model=ActivityTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_activity_template(
    template_id: int,
    payload: ActivityTemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ActivityTemplateResponse:
    template = _service.get_template(db, user.id, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return _service.create_activity_template(db, template, payload)


@router.patch("/{template_id}/activities/{activity_id}", response_model=ActivityTemplateResponse)
async def update_activity_template(
    template_id: int,
    activity_id: int,
    payload: ActivityTemplateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ActivityTemplateResponse:
    template = _service.get_template(db, user.id, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    
    activity = _service.get_activity_template(db, template.id, activity_id)
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity template not found"
        )
        
    return _service.update_activity_template(db, activity, payload)


@router.delete("/{template_id}/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity_template(
    template_id: int,
    activity_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    template = _service.get_template(db, user.id, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
        
    activity = _service.get_activity_template(db, template.id, activity_id)
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity template not found"
        )
        
    _service.delete_activity_template(db, activity)
