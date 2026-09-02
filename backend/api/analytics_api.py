from fastapi import APIRouter, Depends, Query, Response
from typing import Optional

from backend.core.oauth2 import get_current_user
from backend.db.models.core import User
from backend.core.limiter import limiter
from fastapi import Request
from backend.api.deps import get_analytics_service
from backend.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/overview")
@limiter.limit("60/hour")
async def get_overview(
    request: Request,
    response: Response,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    response.headers["Cache-Control"] = "public, max-age=300"
    return await analytics_service.get_overview(user_id=str(current_user.id))

@router.get("/time-patterns")
@limiter.limit("60/hour")
async def get_time_patterns(
    request: Request,
    response: Response,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    response.headers["Cache-Control"] = "public, max-age=300"
    return await analytics_service.get_time_patterns(user_id=str(current_user.id))

@router.get("/calendar-conflicts")
@limiter.limit("60/hour")
async def get_calendar_conflicts(
    request: Request,
    response: Response,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    response.headers["Cache-Control"] = "public, max-age=300"
    return await analytics_service.get_calendar_conflicts(user_id=str(current_user.id))

@router.get("/focus")
@limiter.limit("60/hour")
async def get_focus_metrics(
    request: Request,
    response: Response,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    response.headers["Cache-Control"] = "public, max-age=300"
    return await analytics_service.get_focus_metrics(user_id=str(current_user.id))

@router.get("/ai-effectiveness")
@limiter.limit("60/hour")
async def get_ai_effectiveness(
    request: Request,
    response: Response,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    response.headers["Cache-Control"] = "public, max-age=300"
    return await analytics_service.get_ai_effectiveness(user_id=str(current_user.id))

@router.get("/office-hours")
@limiter.limit("60/hour")
async def get_office_hours(
    request: Request,
    response: Response,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    response.headers["Cache-Control"] = "public, max-age=300"
    # Simplified office hours adherence placeholder
    return []

