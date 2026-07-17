"""API routes for activity history events."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.oauth2 import get_current_user
from backend.db.database import get_db
from backend.db.models.user_table import User
from backend.schemas.history_schema import HistoryEventCreate, HistoryEventResponse
from backend.services.history_service import HistoryService
from backend.services.planner_service import PlannerService

router = APIRouter(prefix="/planners/activities", tags=["history"])
_history_service = HistoryService()
_planner_service = PlannerService()


@router.post(
    "/{activity_id}/history",
    response_model=HistoryEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_history_event(
    activity_id: int,
    payload: HistoryEventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HistoryEventResponse:
    """Create a history event (e.g., status change) on an activity."""
    activity = _planner_service.get_activity(db, user.id, activity_id)
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )

    try:
        event = _history_service.record_event(db, user.id, activity, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return event


@router.get(
    "/{activity_id}/history",
    response_model=list[HistoryEventResponse],
)
async def list_history(
    activity_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[HistoryEventResponse]:
    """List all history events for a given activity, newest first."""
    activity = _planner_service.get_activity(db, user.id, activity_id)
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )

    return _history_service.get_events_for_activity(db, user.id, activity_id)


@router.get(
    "/history/{event_id}",
    response_model=HistoryEventResponse,
)
async def get_history_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HistoryEventResponse:
    """Get a single history event by id."""
    event = _history_service.get_event(db, user.id, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="History event not found"
        )
    return event
