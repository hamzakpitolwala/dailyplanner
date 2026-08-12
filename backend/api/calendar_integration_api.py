"""API endpoints for Google Calendar OAuth integration."""

from datetime import datetime, timezone, timedelta
import logging
from urllib.parse import urlencode, parse_qs, urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
import httpx

from backend.core.config import settings
from backend.core.oauth2 import get_current_user
from backend.core.security import generate_oauth_state, verify_oauth_state
from backend.core.limiter import limiter
from backend.db.models.core import User
from backend.services.integration_service import IntegrationService
from backend.api.deps import get_integration_service, get_task_service
from backend.services.task_service import TaskService
from backend.schemas.core_schema import TaskResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations/google/calendar", tags=["calendar-integration"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


@router.get("/auth-url")
@limiter.limit("10/minute")
async def get_google_calendar_auth_url(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Generate Google OAuth authorization URL for Calendar integration with signed state."""
    if not settings.GOOGLE_CLIENT_ID:
        # Fallback for dev/testing when client ID is not configured
        fake_url = f"{settings.FRONTEND_URL}/#profile?calendar_connected=mock_success"
        return {"url": fake_url}

    redirect_uri = getattr(settings, "GOOGLE_CALENDAR_REDIRECT_URI", "http://127.0.0.1:8000/integrations/google/calendar/callback")

    state_token = generate_oauth_state(str(user.id))
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(CALENDAR_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state_token,
    }
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return {"url": auth_url}


@router.get("/callback")
@limiter.limit("10/minute")
async def google_calendar_callback(
    request: Request,
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
    service: IntegrationService = Depends(get_integration_service),
):
    """Handle OAuth redirect callback from Google with verified state."""
    redirect_target = f"{settings.FRONTEND_URL}/#profile"

    if error or not code:
        logger.warning("Google Calendar OAuth error: %s", error)
        return RedirectResponse(url=f"{redirect_target}?calendar_error={error or 'missing_code'}")

    verified_user_id = verify_oauth_state(state) if state else None
    if not verified_user_id:
        logger.warning("Invalid or expired OAuth state token: %s", state)
        return RedirectResponse(url=f"{redirect_target}?calendar_error=invalid_or_expired_state")

    redirect_uri = getattr(settings, "GOOGLE_CALENDAR_REDIRECT_URI", "http://127.0.0.1:8000/integrations/google/calendar/callback")

    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            if token_resp.status_code != 200:
                logger.error("Token exchange failed (%d): %s", token_resp.status_code, token_resp.text)
                return RedirectResponse(url=f"{redirect_target}?calendar_error=token_exchange_failed")

            data = token_resp.json()
            access_token = data["access_token"]
            refresh_token = data.get("refresh_token", "")
            expires_in = data.get("expires_in", 3600)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            scope_str = data.get("scope", "")
            scopes_list = scope_str.split(" ") if isinstance(scope_str, str) else CALENDAR_SCOPES

            import uuid
            user_id = uuid.UUID(verified_user_id)
            await service.save_oauth_tokens(
                user_id=user_id,
                provider="google",
                access_token=access_token,
                refresh_token=refresh_token,
                scopes=scopes_list,
                expires_at=expires_at,
            )
    except Exception as exc:
        logger.exception("Google Calendar callback exception: %s", exc)
        return RedirectResponse(url=f"{redirect_target}?calendar_error=callback_failed")

    return RedirectResponse(url=f"{redirect_target}?calendar_connected=true")
@router.get("/status")
async def get_google_calendar_status(
    user: User = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    """Check if the authenticated user has connected Google Calendar."""
    token = await service.get_oauth_tokens(user.id, "google") # type: ignore
    if not token:
        return {"connected": False, "scopes": []}

    return {
        "connected": True,
        "provider": "google",
        "scopes": token.scopes,
        "expires_at": token.expires_at,
    }


@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_google_calendar(
    user: User = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    """Disconnect and delete stored Google Calendar OAuth tokens for user."""
    await service.disconnect_provider(user.id, "google") # type: ignore
    return None


@router.post("/sync", response_model=list[TaskResponse])
async def sync_google_calendar(
    target_date: str,
    tz_offset: int = 0,
    user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    """Trigger background Google Calendar sync for target_date and return updated tasks list."""
    await service.sync_google_calendar_for_date(user.id, target_date, tz_offset)
    return await service.list_tasks(user.id, target_date, tz_offset)
