from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.core.oauth2 import get_current_user
from backend.db.database import get_db
from backend.db.models.user_table import User
from backend.schemas.planner_schema import (
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
    DailyPlannerCreate,
    DailyPlannerResponse,
    DailyPlannerUpdate,
)
from backend.services.planner_service import PlannerService

router = APIRouter(prefix="/planners", tags=["planners"])
_service = PlannerService()


@router.get("", response_model=list[DailyPlannerResponse])
async def list_planners(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[DailyPlannerResponse]:
    return _service.list_planners(db, user.id)


@router.get("/today", response_model=DailyPlannerResponse)
async def get_today_planner(
    planner_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyPlannerResponse:
    return _service.get_or_create_planner_for_date(db, user.id, planner_date)


@router.post("", response_model=DailyPlannerResponse, status_code=status.HTTP_201_CREATED)
async def create_planner(
    payload: DailyPlannerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyPlannerResponse:
    try:
        return _service.create_planner(db, user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{planner_id}", response_model=DailyPlannerResponse)
async def get_planner(
    planner_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyPlannerResponse:
    planner = _service.get_planner(db, user.id, planner_id)
    if planner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planner not found")
    return planner


@router.patch("/{planner_id}", response_model=DailyPlannerResponse)
async def update_planner(
    planner_id: int,
    payload: DailyPlannerUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyPlannerResponse:
    planner = _service.get_planner(db, user.id, planner_id)
    if planner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planner not found")
    return _service.update_planner(db, planner, payload)


@router.delete("/{planner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planner(
    planner_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    planner = _service.get_planner(db, user.id, planner_id)
    if planner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planner not found")
    _service.delete_planner(db, planner)


@router.post(
    "/{planner_id}/activities",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_activity(
    planner_id: int,
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ActivityResponse:
    planner = _service.get_planner(db, user.id, planner_id)
    if planner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planner not found")
    return _service.create_activity(db, planner, payload)


@router.patch("/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: int,
    payload: ActivityUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ActivityResponse:
    activity = _service.get_activity(db, user.id, activity_id)
    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return _service.update_activity(db, activity, payload)


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    activity = _service.get_activity(db, user.id, activity_id)
    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    _service.delete_activity(db, activity)
