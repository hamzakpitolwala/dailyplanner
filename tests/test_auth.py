"""Integration tests for the auth flow: register → login → /auth/me + OAuth2.

Aligned with the refactored backend:
- UserCreate no longer has `username` (removed from model).
- User.hashed_password replaces password_hash; nullable for OAuth-only accounts.
- AuthService exposes find_or_create_oauth_user instead of a legacy method.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.core.oauth2_providers import OAuthUserInfo
from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register(email: str, password: str = "secret1234") -> dict:
    """Register a user and return the response JSON."""
    return client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )


def _login(email: str, password: str = "secret1234") -> dict:
    return client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health_endpoint():
    """Smoke test that the app boots and /health returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_returns_user():
    response = _register("alice@example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@example.com"
    # id should be a valid UUID string
    assert "id" in data
    assert "-" in data["id"]
    # password must never be exposed
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_email_fails():
    _register("dup@example.com")
    response = _register("dup@example.com")
    assert response.status_code == 400


def test_register_short_password_fails():
    """Password shorter than 8 chars should fail Pydantic validation (422)."""
    response = _register("short@example.com", password="abc")
    assert response.status_code == 422


def test_register_without_username_succeeds():
    """New schema has no `username` field — omitting it should be fine."""
    response = client.post(
        "/auth/register",
        json={"email": "nousername@example.com", "password": "secret1234"},
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def test_login_returns_token():
    _register("bob@example.com")
    response = _login("bob@example.com")
    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"


def test_login_wrong_password_fails():
    _register("carol@example.com")
    response = client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_login_unknown_email_fails():
    response = _login("nobody@example.com")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------


def test_me_returns_current_user():
    _register("dave@example.com")
    token = _login("dave@example.com").json()["access_token"]

    me_resp = client.get("/auth/me", headers=_auth_headers(token))
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["email"] == "dave@example.com"
    assert "hashed_password" not in data


def test_me_without_token_fails():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_with_invalid_token_fails():
    response = client.get("/auth/me", headers=_auth_headers("not.a.valid.jwt"))
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# OAuth2 provider stubs
# ---------------------------------------------------------------------------


def test_google_authorize_not_configured():
    """Without GOOGLE_CLIENT_ID, the endpoint returns 501."""
    response = client.get("/auth/google/authorize", follow_redirects=False)
    assert response.status_code == 501


def test_github_authorize_not_configured():
    """Without GITHUB_CLIENT_ID, the endpoint returns 501."""
    response = client.get("/auth/github/authorize", follow_redirects=False)
    assert response.status_code == 501


@patch("backend.api.oauth2_api.GoogleOAuth2.fetch_user", new_callable=AsyncMock)
def test_google_callback_creates_user(mock_fetch):
    """Simulate a successful Google callback creating a new user."""
    mock_fetch.return_value = OAuthUserInfo(
        email="googleuser@example.com",
        name="Google User",
        provider="google",
        provider_id="g-12345",
    )

    response = client.get(
        "/auth/google/callback?code=test-code&state=test-state",
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert "token=" in response.headers["location"]


@patch("backend.api.oauth2_api.GitHubOAuth2.fetch_user", new_callable=AsyncMock)
def test_github_callback_creates_user(mock_fetch):
    """Simulate a successful GitHub callback creating a new user."""
    mock_fetch.return_value = OAuthUserInfo(
        email="githubuser@example.com",
        name="GitHub User",
        provider="github",
        provider_id="gh-67890",
    )

    response = client.get(
        "/auth/github/callback?code=test-code&state=test-state",
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert "token=" in response.headers["location"]


@patch("backend.api.oauth2_api.GoogleOAuth2.fetch_user", new_callable=AsyncMock)
def test_oauth_links_existing_email_account(mock_fetch):
    """If a user registered with email, OAuth login with the same email links the account."""
    _register("linked@example.com")

    mock_fetch.return_value = OAuthUserInfo(
        email="linked@example.com",
        name="Linked User",
        provider="google",
        provider_id="g-linked",
    )

    response = client.get(
        "/auth/google/callback?code=test-code&state=test-state",
        follow_redirects=False,
    )
    assert response.status_code == 307
    token = response.headers["location"].split("token=")[1]

    me_resp = client.get("/auth/me", headers=_auth_headers(token))
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "linked@example.com"


@patch("backend.api.oauth2_api.GitHubOAuth2.fetch_user", new_callable=AsyncMock)
def test_oauth_user_cannot_password_login(mock_fetch):
    """OAuth-only users (no hashed_password) should not be able to login with password."""
    mock_fetch.return_value = OAuthUserInfo(
        email="oauthonly@example.com",
        name="OAuth Only",
        provider="github",
        provider_id="gh-only",
    )
    client.get(
        "/auth/github/callback?code=test-code&state=test-state",
        follow_redirects=False,
    )

    response = _login("oauthonly@example.com", password="anything")
    assert response.status_code == 401


@patch("backend.api.oauth2_api.GoogleOAuth2.fetch_user", new_callable=AsyncMock)
def test_oauth_same_provider_reuses_account(mock_fetch):
    """A second OAuth login for the same provider_id returns the same user (no duplicate)."""
    user_info = OAuthUserInfo(
        email="reuse@example.com",
        name="Reuse User",
        provider="google",
        provider_id="g-reuse-99",
    )
    mock_fetch.return_value = user_info

    # First login — creates the account
    client.get("/auth/google/callback?code=c1&state=s1", follow_redirects=False)

    # Second login — must reuse the same user
    resp2 = client.get("/auth/google/callback?code=c2&state=s2", follow_redirects=False)
    token = resp2.headers["location"].split("token=")[1]

    me = client.get("/auth/me", headers=_auth_headers(token)).json()
    assert me["email"] == "reuse@example.com"
