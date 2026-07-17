"""Integration tests for the auth flow: register → login → /auth/me + OAuth2."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.core.oauth2_providers import OAuthUserInfo
from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Email/password auth tests
# ---------------------------------------------------------------------------


def test_health_endpoint():
    """Smoke test that the app boots and /health returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_returns_user():
    response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "username": "alice", "password": "secret1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["username"] == "alice"
    assert "id" in data


def test_register_duplicate_email_fails():
    client.post(
        "/auth/register",
        json={"email": "dup@example.com", "username": "dup1", "password": "secret1234"},
    )
    response = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "username": "dup2", "password": "secret1234"},
    )
    assert response.status_code == 400


def test_register_short_password_fails():
    response = client.post(
        "/auth/register",
        json={"email": "short@example.com", "username": "short", "password": "abc"},
    )
    assert response.status_code == 422  # pydantic validation error


def test_login_returns_token():
    client.post(
        "/auth/register",
        json={"email": "bob@example.com", "username": "bob", "password": "secret1234"},
    )
    response = client.post(
        "/auth/login",
        json={"email": "bob@example.com", "password": "secret1234"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"


def test_login_wrong_password_fails():
    client.post(
        "/auth/register",
        json={"email": "carol@example.com", "username": "carol", "password": "secret1234"},
    )
    response = client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_me_returns_current_user():
    client.post(
        "/auth/register",
        json={"email": "dave@example.com", "username": "dave", "password": "secret1234"},
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": "dave@example.com", "password": "secret1234"},
    )
    token = login_resp.json()["access_token"]

    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "dave@example.com"


def test_me_without_token_fails():
    response = client.get("/auth/me")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# OAuth2 tests
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
    # Should redirect to frontend with a token in the hash
    assert response.status_code == 307
    location = response.headers["location"]
    assert "token=" in location


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
    location = response.headers["location"]
    assert "token=" in location


@patch("backend.api.oauth2_api.GoogleOAuth2.fetch_user", new_callable=AsyncMock)
def test_oauth_links_existing_email_account(mock_fetch):
    """If a user registered with email, OAuth login with the same email links the account."""
    # First register via email/password
    client.post(
        "/auth/register",
        json={"email": "linked@example.com", "username": "linked", "password": "secret1234"},
    )

    # Now sign in via Google with the same email
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
    location = response.headers["location"]
    assert "token=" in location

    # Verify the user still works with the JWT from OAuth
    token = location.split("token=")[1]
    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "linked@example.com"


@patch("backend.api.oauth2_api.GitHubOAuth2.fetch_user", new_callable=AsyncMock)
def test_oauth_user_cannot_password_login(mock_fetch):
    """OAuth-only users should not be able to login with password."""
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

    # Try password login — should fail
    response = client.post(
        "/auth/login",
        json={"email": "oauthonly@example.com", "password": "anything"},
    )
    assert response.status_code == 401
