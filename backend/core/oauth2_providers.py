"""Google and GitHub OAuth2 provider helpers.

Each provider class knows how to:
1. Build the authorization redirect URL
2. Exchange an authorization code for an access token
3. Fetch the authenticated user's profile (email + name)
"""

import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from backend.core.config import settings


@dataclass(frozen=True)
class OAuthUserInfo:
    """Normalized user profile returned by any provider."""

    email: str
    name: str
    provider: str
    provider_id: str


class OAuth2Provider(ABC):
    """Abstract Strategy class for OAuth2 providers."""

    @abstractmethod
    def authorize_url(self, redirect_uri: str) -> tuple[str, str]:
        """Return the authorization redirect URL and the CSRF state string."""
        pass

    @abstractmethod
    async def fetch_user(self, code: str, redirect_uri: str) -> OAuthUserInfo:
        """Exchange the code for a token and fetch/return the user's profile."""
        pass


# ---------------------------------------------------------------------------
# Google
# ---------------------------------------------------------------------------

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleOAuth2Provider(OAuth2Provider):
    """Google OAuth2 Authorization Code flow strategy."""

    def authorize_url(self, redirect_uri: str) -> tuple[str, str]:
        """Return the full Google consent-screen URL."""
        state = secrets.token_urlsafe(32)
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": state,
        }
        return f"{_GOOGLE_AUTH_URL}?{urlencode(params)}", state

    async def fetch_user(self, code: str, redirect_uri: str) -> OAuthUserInfo:
        """Exchange *code* for a token and return the user's profile."""
        async with httpx.AsyncClient(timeout=10) as client:
            # Step 1: code → access_token
            token_resp = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()["access_token"]

            # Step 2: access_token → user info
            user_resp = await client.get(
                _GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_resp.raise_for_status()
            data = user_resp.json()

        return OAuthUserInfo(
            email=data["email"],
            name=data.get("name", data["email"].split("@")[0]),
            provider="google",
            provider_id=str(data["id"]),
        )


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

_GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"
_GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


class GitHubOAuth2Provider(OAuth2Provider):
    """GitHub OAuth2 Authorization Code flow strategy."""

    def authorize_url(self, redirect_uri: str) -> tuple[str, str]:
        """Return the full GitHub authorization URL."""
        state = secrets.token_urlsafe(32)
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
        return f"{_GITHUB_AUTH_URL}?{urlencode(params)}", state

    async def fetch_user(self, code: str, redirect_uri: str) -> OAuthUserInfo:
        """Exchange *code* for a token and return the user's profile."""
        async with httpx.AsyncClient(timeout=10) as client:
            # Step 1: code → access_token
            token_resp = await client.post(
                _GITHUB_TOKEN_URL,
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()["access_token"]

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            # Step 2: fetch profile
            user_resp = await client.get(_GITHUB_USER_URL, headers=headers)
            user_resp.raise_for_status()
            profile = user_resp.json()

            # Step 3: fetch primary email (may not be in profile)
            email = profile.get("email")
            if not email:
                emails_resp = await client.get(_GITHUB_EMAILS_URL, headers=headers)
                emails_resp.raise_for_status()
                for entry in emails_resp.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry["email"]
                        break

            if not email:
                raise ValueError("GitHub account has no verified primary email")

        return OAuthUserInfo(
            email=email,
            name=profile.get("name") or profile.get("login", email.split("@")[0]),
            provider="github",
            provider_id=str(profile["id"]),
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class OAuth2ProviderFactory:
    """Factory to retrieve OAuth2 provider strategy instances."""

    _providers = {
        "google": GoogleOAuth2Provider(),
        "github": GitHubOAuth2Provider(),
    }

    @classmethod
    def get_provider(cls, provider: str) -> OAuth2Provider:
        """Get provider strategy instance by name."""
        name = provider.lower()
        if name not in cls._providers:
            raise ValueError(f"Unsupported OAuth2 provider: {provider}")
        return cls._providers[name]
