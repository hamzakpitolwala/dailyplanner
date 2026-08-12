import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.agents.chat_agent import PersonalizedChatAgent
from backend.schemas.ai_engine_schema import ChatMessage

@pytest.mark.asyncio
async def test_chat_agent_conversational():
    agent = PersonalizedChatAgent()
    agent.llm_client.chat = AsyncMock(return_value="Hello! I am your AI assistant.")
    
    # Mock services
    mock_user_service = MagicMock()
    mock_task_service = MagicMock()
    mock_fixed_block_repo = MagicMock()
    
    # Mock async get_or_fetch_context
    agent.get_or_fetch_context = AsyncMock(return_value="User context data")

    messages = [ChatMessage(role="user", content="Hi!")]
    reply, s_type, s_data = await agent.chat(
        user_id=uuid.uuid4(),
        messages=messages,
        user_service=mock_user_service,
        task_service=mock_task_service,
        fixed_block_repo=mock_fixed_block_repo
    )
    
    assert reply == "Hello! I am your AI assistant."
    assert s_type is None
    assert s_data is None


@pytest.mark.asyncio
async def test_chat_agent_structured_json():
    agent = PersonalizedChatAgent()
    
    # Simulate LLM returning a structured JSON block inside markdown
    json_response = """
Here is your plan!
```json
{
  "structuredType": "starter",
  "structuredData": {
    "template_name": "My Plan",
    "description": "A great plan",
    "activities": []
  }
}
```
Enjoy!
    """
    agent.llm_client.chat = AsyncMock(return_value=json_response)
    
    # Mock services
    mock_user_service = MagicMock()
    mock_task_service = MagicMock()
    mock_fixed_block_repo = MagicMock()
    
    # Mock async get_or_fetch_context
    agent.get_or_fetch_context = AsyncMock(return_value="User context data")

    messages = [ChatMessage(role="user", content="Give me a starter plan")]
    reply, s_type, s_data = await agent.chat(
        user_id=uuid.uuid4(),
        messages=messages,
        user_service=mock_user_service,
        task_service=mock_task_service,
        fixed_block_repo=mock_fixed_block_repo
    )
    
    assert "Here is your plan!" in reply
    assert "Enjoy!" in reply
    assert "```json" not in reply
    
    assert s_type == "starter"
    assert s_data["template_name"] == "My Plan"
    assert s_data["description"] == "A great plan"
    assert s_data["activities"] == []
