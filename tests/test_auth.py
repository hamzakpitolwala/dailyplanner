import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
"""Integration tests for the auth flow: register → login → /auth/me + OAuth2.

Aligned with the refactored backend:
- UserCreate no longer has `username` (removed from model).
- User.hashed_password replaces password_hash; nullable for OAuth-only accounts.
- AuthService exposes find_or_create_oauth_user instead of a legacy method.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


from backend.core.oauth2_providers import OAuthUserInfo
from backend.main import app

client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register(email: str, password: str = "secret1234") -> dict:
    return await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )


async def _login(email: str, password: str = "secret1234") -> dict:
    return await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint():
    """Smoke test that the app boots and /health returns ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_returns_user():
    response = await _register("alice@example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@example.com"
    # id should be a valid UUID string
    assert "id" in data
    assert "-" in data["id"]
    # password must never be exposed
    assert "hashed_password" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_fails():
    await _register("dup@example.com")
    response = await _register("dup@example.com")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_short_password_fails():
    """Password shorter than 8 chars should fail Pydantic validation (422)."""
    response = await _register("short@example.com", password="abc")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_without_username_succeeds():
    """New schema has no `username` field — omitting it should be fine."""
    response = await client.post(
        "/auth/register",
        json={"email": "nousername@example.com", "password": "secret1234"},
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_returns_token():
    await _register("bob@example.com")
    response = await _login("bob@example.com")
    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_fails():
    await _register("carol@example.com")
    response = await client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email_fails():
    response = await _login("nobody@example.com")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_me_returns_current_user():
    await _register("dave@example.com")
    token = (await _login("dave@example.com")).json()["access_token"]

    me_resp = await client.get("/auth/me", headers=_auth_headers(token))
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["email"] == "dave@example.com"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_me_without_token_fails():
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_fails():
    response = await client.get("/auth/me", headers=_auth_headers("not.a.valid.jwt"))
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# OAuth2 provider stubs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_google_authorize_not_configured():
    """Without GOOGLE_CLIENT_ID, the endpoint redirects to frontend with error."""
    response = await client.get("/auth/google/authorize", follow_redirects=False)
    assert response.status_code == 307
    assert "error=google_oauth_not_configured" in response.headers["location"]


@pytest.mark.asyncio
async def test_github_authorize_not_configured():
    """Without GITHUB_CLIENT_ID, the endpoint redirects to frontend with error."""
    response = await client.get("/auth/github/authorize", follow_redirects=False)
    assert response.status_code == 307
    assert "error=github_oauth_not_configured" in response.headers["location"]


@patch("backend.api.oauth2_api.OAuth2ProviderFactory.get_provider")
@pytest.mark.asyncio
async def test_google_callback_creates_user(mock_get_provider):
    """Simulate a successful Google callback creating a new user."""
    mock_provider = MagicMock()
    mock_provider.fetch_user = AsyncMock(return_value=OAuthUserInfo(
        email="googleuser@example.com",
        name="Google User",
        provider="google",
        provider_id="g-12345",
    ))
    mock_get_provider.return_value = mock_provider

    response = await client.get(
        "/auth/google/callback?code=test-code&state=test-state",
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert "token=" in response.headers["location"]


@patch("backend.api.oauth2_api.OAuth2ProviderFactory.get_provider")
@pytest.mark.asyncio
async def test_github_callback_creates_user(mock_get_provider):
    """Simulate a successful GitHub callback creating a new user."""
    mock_provider = MagicMock()
    mock_provider.fetch_user = AsyncMock(return_value=OAuthUserInfo(
        email="githubuser@example.com",
        name="GitHub User",
        provider="github",
        provider_id="gh-67890",
    ))
    mock_get_provider.return_value = mock_provider

    response = await client.get(
        "/auth/github/callback?code=test-code&state=test-state",
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert "token=" in response.headers["location"]


@patch("backend.api.oauth2_api.OAuth2ProviderFactory.get_provider")
@pytest.mark.asyncio
async def test_oauth_links_existing_email_account(mock_get_provider):
    """If a user registered with email, OAuth login with the same email links the account."""
    await _register("linked@example.com")

    mock_provider = MagicMock()
    mock_provider.fetch_user = AsyncMock(return_value=OAuthUserInfo(
        email="linked@example.com",
        name="Linked User",
        provider="google",
        provider_id="g-linked",
    ))
    mock_get_provider.return_value = mock_provider

    response = await client.get(
        "/auth/google/callback?code=test-code&state=test-state",
        follow_redirects=False,
    )
    assert response.status_code == 307
    token = response.headers["location"].split("token=")[1]

    me_resp = await client.get("/auth/me", headers=_auth_headers(token))
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "linked@example.com"


@patch("backend.api.oauth2_api.OAuth2ProviderFactory.get_provider")
@pytest.mark.asyncio
async def test_oauth_user_cannot_password_login(mock_get_provider):
    """OAuth-only users (no hashed_password) should not be able to login with password."""
    mock_provider = MagicMock()
    mock_provider.fetch_user = AsyncMock(return_value=OAuthUserInfo(
        email="oauthonly@example.com",
        name="OAuth Only",
        provider="github",
        provider_id="gh-only",
    ))
    mock_get_provider.return_value = mock_provider
    await client.get(
        "/auth/github/callback?code=test-code&state=test-state",
        follow_redirects=False,
    )

    response = await _login("oauthonly@example.com", password="anything")
    assert response.status_code == 401


@patch("backend.api.oauth2_api.OAuth2ProviderFactory.get_provider")
@pytest.mark.asyncio
async def test_oauth_same_provider_reuses_account(mock_get_provider):
    """A second OAuth login for the same provider_id returns the same user (no duplicate)."""
    user_info = OAuthUserInfo(
        email="reuse@example.com",
        name="Reuse User",
        provider="google",
        provider_id="g-reuse-99",
    )
    mock_provider = MagicMock()
    mock_provider.fetch_user = AsyncMock(return_value=user_info)
    mock_get_provider.return_value = mock_provider

    # First login — creates the account
    await client.get("/auth/google/callback?code=c1&state=s1", follow_redirects=False)

    # Second login — must reuse the same user
    resp2 = await client.get("/auth/google/callback?code=c2&state=s2", follow_redirects=False)
    token = resp2.headers["location"].split("token=")[1]

    me = (await client.get("/auth/me", headers=_auth_headers(token))).json()
    assert me["email"] == "reuse@example.com"


@pytest.mark.asyncio
async def test_get_and_update_user_profile():
    """Verify GET and PUT /users/me/profile return 200 without validation errors."""
    reg = (await _register("profile_test@example.com")).json()
    login_res = (await _login("profile_test@example.com")).json()
    token = login_res["access_token"]
    headers = _auth_headers(token)

    # GET profile
    get_res = await client.get("/users/me/profile", headers=headers)
    assert get_res.status_code == 200
    prof_data = get_res.json()
    assert "id" in prof_data
    assert "user_id" in prof_data

    # PUT update profile
    put_res = await client.put(
        "/users/me/profile",
        json={"username": "profile_user_1", "goals": "Build great software"},
        headers=headers,
    )
    assert put_res.status_code == 200
    updated_data = put_res.json()
    assert updated_data["username"] == "profile_user_1"
    assert updated_data["goals"] == "Build great software"
