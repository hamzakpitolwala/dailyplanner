"""OAuth2 social login routes for Google and GitHub."""

import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import RedirectResponse

from backend.core.config import settings
from backend.core.jwt import create_access_token
from backend.core.limiter import limiter
from backend.core.oauth2_providers import OAuth2ProviderFactory, OAuthUserInfo
from backend.services.auth_services import AuthService
from backend.api.deps import get_auth_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["oauth2"])


# ---------------------------------------------------------------------------
# Google
# ---------------------------------------------------------------------------


@router.get("/google/authorize")
@limiter.limit("10/minute")
async def google_authorize(request: Request):
    """Redirect the user to Google's consent screen."""
    if not settings.GOOGLE_CLIENT_ID:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/#auth?error=google_oauth_not_configured"
        )
    provider = OAuth2ProviderFactory.get_provider("google")
    url, state = provider.authorize_url(settings.GOOGLE_REDIRECT_URI)
    return RedirectResponse(url=url)


@router.get("/google/callback", name="google_callback")
async def google_callback(
    code: str | None = None,
    error: str | None = None,
    service: AuthService = Depends(get_auth_service),
):
    """Handle Google's redirect after user consent."""
    if error or not code:
        logger.warning("Google OAuth2 error: %s", error)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/#error={error or 'missing_code'}"
        )

    try:
        provider = OAuth2ProviderFactory.get_provider("google")
        user_info = await provider.fetch_user(code, settings.GOOGLE_REDIRECT_URI)
    except Exception as exc:
        logger.exception("Google OAuth2 token exchange failed")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/#error=oauth_failed"
        )

    return await _complete_oauth_login(service, user_info)


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------


@router.get("/github/authorize")
@limiter.limit("10/minute")
async def github_authorize(request: Request):
    """Redirect the user to GitHub's authorization page."""
    if not settings.GITHUB_CLIENT_ID:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/#auth?error=github_oauth_not_configured"
        )
    provider = OAuth2ProviderFactory.get_provider("github")
    url, state = provider.authorize_url(settings.GITHUB_REDIRECT_URI)
    return RedirectResponse(url=url)


@router.get("/github/callback", name="github_callback")
async def github_callback(
    code: str | None = None,
    error: str | None = None,
    service: AuthService = Depends(get_auth_service),
):
    """Handle GitHub's redirect after user authorization."""
    if error or not code:
        logger.warning("GitHub OAuth2 error: %s", error)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/#error={error or 'missing_code'}"
        )

    try:
        provider = OAuth2ProviderFactory.get_provider("github")
        user_info = await provider.fetch_user(code, settings.GITHUB_REDIRECT_URI)
    except Exception as exc:
        logger.exception("GitHub OAuth2 token exchange failed")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/#error=oauth_failed"
        )

    return await _complete_oauth_login(service, user_info)


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


async def _complete_oauth_login(service: AuthService, info: OAuthUserInfo) -> RedirectResponse:
    """Find or create the user, issue a JWT, and redirect to the frontend."""
    try:
        user = await service.find_or_create_oauth_user(
            email=info.email,
            provider=info.provider,
            provider_id=info.provider_id,
            username=info.name,
        )
    except ValueError as exc:
        logger.error("OAuth2 user creation failed: %s", exc)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/#error=account_error"
        )

    token = create_access_token({"sub": str(user.id), "email": user.email})
    params = urlencode({"token": token})
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/#{params}")