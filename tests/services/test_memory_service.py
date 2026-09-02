import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from backend.services.memory_service import MemoryService
from backend.services.llm_client import BaseLLMClient

class MockMemoryLLMClient(BaseLLMClient):
    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        return '{"extracted_memories": [{"content": "Loves hiking", "category": "preference", "scope": "user_profile"}]}'

@pytest.mark.asyncio
async def test_extract_and_store_memories():
    mock_manager = AsyncMock()
    client = MockMemoryLLMClient()
    service = MemoryService(mock_manager, client)
    
    await service.extract_and_store_memories(uuid4(), uuid4(), "I love hiking on weekends", "Great, I'll add a hike task.")
    
    # Check if add_memory was called
    mock_manager.add_memory.assert_called_once()
    args, kwargs = mock_manager.add_memory.call_args
    assert kwargs["content"] == "Loves hiking"
    assert kwargs["scope"] == "user_profile"

@pytest.mark.asyncio
async def test_consolidate_session_memories():
    mock_manager = AsyncMock()
    mock_memory = MagicMock()
    mock_memory.content = "Temporary session note"
    mock_manager.get_memories.return_value = [mock_memory]
    
    client = MockMemoryLLMClient()
    service = MemoryService(mock_manager, client)
    
    await service.consolidate_session_memories(uuid4(), uuid4())
    
    # Check if add_memory was called for consolidated memory
    mock_manager.add_memory.assert_called_once()
    args, kwargs = mock_manager.add_memory.call_args
    assert kwargs["content"] == "Loves hiking"
