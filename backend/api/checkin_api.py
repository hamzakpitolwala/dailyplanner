"""API routes for activity check-ins."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.oauth2 import get_current_user
from backend.db.database import get_db
from backend.db.models.user_table import User
from backend.schemas.checkin_schema import CheckinCreate, CheckinResponse
from backend.services.checkin_service import CheckinService
from backend.services.planner_service import PlannerService

router = APIRouter(prefix="/planners/activities", tags=["checkins"])
_checkin_service = CheckinService()
_planner_service = PlannerService()


@router.post(
    "/{activity_id}/checkins",
    response_model=CheckinResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_checkin(
    activity_id: int,
    payload: CheckinCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CheckinResponse:
    """Create a check-in on an activity.

    When the status is ``not_done``, the payload may include a
    ``missed_reason`` and/or ``alternate_activity`` depending on
    the activity's policy.
    """
    activity = _planner_service.get_activity(db, user.id, activity_id)
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )

    try:
        checkin = _checkin_service.create_checkin(db, user.id, activity, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return checkin


@router.get(
    "/{activity_id}/checkins",
    response_model=list[CheckinResponse],
)
async def list_checkins(
    activity_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CheckinResponse]:
    """List all check-ins for a given activity, newest first."""
    activity = _planner_service.get_activity(db, user.id, activity_id)
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )

    return _checkin_service.get_checkins_for_activity(db, user.id, activity_id)


@router.get(
    "/checkins/{checkin_id}",
    response_model=CheckinResponse,
)
async def get_checkin(
    checkin_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CheckinResponse:
    """Get a single check-in by id."""
    checkin = _checkin_service.get_checkin(db, user.id, checkin_id)
    if checkin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found"
        )
    return checkin
