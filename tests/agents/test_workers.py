import pytest
from uuid import uuid4
from backend.agents.workers.conversation import ConversationWorker
from backend.services.llm_client import BaseLLMClient

class MockLLMClient(BaseLLMClient):
    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        return "mocked response"

@pytest.mark.asyncio
async def test_conversation_worker():
    client = MockLLMClient()
    worker = ConversationWorker(client)
    
    result = await worker.process(
        user_id=uuid4(),
        message="Hello!",
        context={},
        intent={"type": "conversation"}
    )
    
    assert result["status"] == "completed"
    assert result["explanation"] == "mocked response"
