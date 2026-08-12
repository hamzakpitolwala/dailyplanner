import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
"""Unit tests for backend core utilities: security, JWT, and OAuth2 providers.

Covers:
- Password hashing & verification (bcrypt + legacy pbkdf2 format)
- JWT token encoding, decoding, payload extraction, invalid token handling
- OAuth2 providers (URL generation, state parameter, user info fetching with HTTP mocks)
"""

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from jose import JWTError

from backend.core.jwt import create_access_token, decode_access_token
from backend.core.oauth2_providers import GoogleOAuth2Provider, GitHubOAuth2Provider, OAuthUserInfo
from backend.core.security import hash_password, verify_password

GoogleOAuth2 = GoogleOAuth2Provider()
GitHubOAuth2 = GitHubOAuth2Provider()



class TestSecurity:
    @pytest.mark.asyncio
    async def test_hash_and_verify_password(self):
        pwd = "my_secret_password_123"
        hashed = hash_password(pwd)

        assert hashed != pwd
        assert verify_password(pwd, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    @pytest.mark.asyncio
    async def test_verify_legacy_pbkdf2_password(self):
        password = "legacy_secret"
        salt = "testsalt"
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
        ).hex()
        legacy_hash = f"pbkdf2_sha256${salt}${digest}"

        assert verify_password(password, legacy_hash) is True
        assert verify_password("wrong_password", legacy_hash) is False
        assert verify_password(password, "pbkdf2_sha256$badformat") is False


class TestJWT:
    @pytest.mark.asyncio
    async def test_create_and_decode_access_token(self):
        data = {"sub": "user_id_123", "role": "user"}
        token = create_access_token(data)

        assert isinstance(token, str)
        decoded = decode_access_token(token)
        assert decoded["sub"] == "user_id_123"
        assert decoded["role"] == "user"
        assert "exp" in decoded

    @pytest.mark.asyncio
    async def test_decode_invalid_token_raises_error(self):
        with pytest.raises(JWTError):
            decode_access_token("invalid.jwt.token")


class TestOAuth2Providers:
    @pytest.mark.asyncio
    async def test_google_authorize_url(self):
        url, state = GoogleOAuth2.authorize_url("http://localhost:5173/auth/callback")
        assert "accounts.google.com" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%3A5173%2Fauth%2Fcallback" in url
        assert len(state) > 10

    @pytest.mark.asyncio
    async def test_github_authorize_url(self):
        url, state = GitHubOAuth2.authorize_url("http://localhost:5173/auth/callback")
        assert "github.com/login/oauth/authorize" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%3A5173%2Fauth%2Fcallback" in url
        assert len(state) > 10

    @pytest.mark.asyncio
    async def test_google_fetch_user(self):
        import asyncio

        mock_token_resp = MagicMock()
        mock_token_resp.raise_for_status = MagicMock()
        mock_token_resp.json = MagicMock(return_value={"access_token": "g_token"})

        mock_user_resp = MagicMock()
        mock_user_resp.raise_for_status = MagicMock()
        mock_user_resp.json = MagicMock(
            return_value={"id": "g_12345", "email": "guser@example.com", "name": "Google User"}
        )

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_token_resp
        mock_client.get.return_value = mock_user_resp

        with patch("httpx.AsyncClient", return_value=mock_client):
            user_info = await GoogleOAuth2.fetch_user("code_123", "http://localhost/callback")
            assert isinstance(user_info, OAuthUserInfo)
            assert user_info.email == "guser@example.com"
            assert user_info.name == "Google User"
            assert user_info.provider == "google"
            assert user_info.provider_id == "g_12345"

    @pytest.mark.asyncio
    async def test_github_fetch_user(self):
        import asyncio

        mock_token_resp = MagicMock()
        mock_token_resp.raise_for_status = MagicMock()
        mock_token_resp.json = MagicMock(return_value={"access_token": "gh_token"})

        mock_user_resp = MagicMock()
        mock_user_resp.raise_for_status = MagicMock()
        mock_user_resp.json = MagicMock(
            return_value={"id": 9876, "login": "ghuser", "name": "GitHub User", "email": None}
        )

        mock_emails_resp = MagicMock()
        mock_emails_resp.raise_for_status = MagicMock()
        mock_emails_resp.json = MagicMock(
            return_value=[
                {"email": "secondary@example.com", "primary": False, "verified": True},
                {"email": "primary@example.com", "primary": True, "verified": True},
            ]
        )

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_token_resp
        mock_client.get.side_effect = [mock_user_resp, mock_emails_resp]

        with patch("httpx.AsyncClient", return_value=mock_client):
            user_info = await GitHubOAuth2.fetch_user("code_456", "http://localhost/callback")
            assert isinstance(user_info, OAuthUserInfo)
            assert user_info.email == "primary@example.com"
            assert user_info.name == "GitHub User"
            assert user_info.provider == "github"
            assert user_info.provider_id == "9876"
