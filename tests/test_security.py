import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.core.security import generate_oauth_state, verify_oauth_state
from backend.core.config import settings


@pytest.mark.asyncio
async def test_security_headers_present():
    """Verify all OWASP recommended security headers are present on API responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        headers = response.headers

        assert "Content-Security-Policy" in headers
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in headers
        assert "Referrer-Policy" in headers
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Permissions-Policy" in headers


class TestOAuthStateHMAC:
    def test_generate_and_verify_valid_state(self):
        user_id = str(uuid.uuid4())
        state = generate_oauth_state(user_id)
        
        verified_id = verify_oauth_state(state)
        assert verified_id == user_id

    def test_verify_forged_state_fails(self):
        user_id = str(uuid.uuid4())
        state = generate_oauth_state(user_id)
        
        # Tamper with the user ID in the state string
        parts = state.split(":")
        tampered_state = f"{uuid.uuid4()}:{parts[1]}:{parts[2]}"

        verified_id = verify_oauth_state(tampered_state)
        assert verified_id is None

    def test_verify_expired_state_fails(self):
        user_id = str(uuid.uuid4())
        # State created 1000 seconds ago
        old_timestamp = "1000000000"
        import hmac, hashlib
        msg = f"{user_id}:{old_timestamp}".encode("utf-8")
        sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        expired_state = f"{user_id}:{old_timestamp}:{sig}"

        verified_id = verify_oauth_state(expired_state, max_age_seconds=600)
        assert verified_id is None


@pytest.mark.asyncio
async def test_rate_limiting_auth_endpoints():
    """Verify rate limits kick in for sensitive authentication routes."""
    from backend.core.limiter import limiter
    limiter.enabled = True
    try:
        transport = ASGITransport(app=app, client=("127.0.0.1", 12345))
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            responses = []
            for i in range(15):
                res = await client.post(
                    "/auth/register",
                    json={
                        "email": f"ratelimit_{i}@example.com",
                        "password": "Password123!",
                        "timezone": "UTC"
                    }
                )
                responses.append(res.status_code)

            # 429 Too Many Requests should be triggered after rate limit (5/minute)
            assert 429 in responses
    finally:
        limiter.enabled = False
