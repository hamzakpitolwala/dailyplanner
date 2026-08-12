import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from backend.main import app
from backend.db.models.core import User
from backend.api.deps import get_user_service, get_task_service, get_fixed_block_repository
from backend.core.oauth2 import get_current_user

# Use TestClient
client = TestClient(app)

@pytest.fixture(autouse=True)
def override_deps():
    app.dependency_overrides[get_current_user] = lambda: User(id=str(uuid.uuid4()), email="test@example.com")
    app.dependency_overrides[get_user_service] = lambda: MagicMock()
    app.dependency_overrides[get_task_service] = lambda: MagicMock()
    app.dependency_overrides[get_fixed_block_repository] = lambda: MagicMock()
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_user_service, None)
    app.dependency_overrides.pop(get_task_service, None)
    app.dependency_overrides.pop(get_fixed_block_repository, None)


@pytest.mark.asyncio
async def test_ai_chat_endpoint_conversational():
    with patch("backend.api.ai_api.chat_agent.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = ("Hello, how can I help?", None, None)
        
        response = client.post("/ai/chat", json={
            "messages": [
                {"role": "user", "content": "Hi"}
            ]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Hello, how can I help?"
        assert data["structuredType"] is None
        assert data["structuredData"] is None


@pytest.mark.asyncio
async def test_ai_chat_endpoint_structured():
    with patch("backend.api.ai_api.chat_agent.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = (
            "Here is your plan!", 
            "starter", 
            {"template_name": "Plan", "description": "", "activities": []}
        )
        
        response = client.post("/ai/chat", json={
            "messages": [
                {"role": "user", "content": "Make a plan"}
            ]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Here is your plan!"
        assert data["structuredType"] == "starter"
        assert data["structuredData"]["template_name"] == "Plan"
