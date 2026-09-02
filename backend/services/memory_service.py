import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from backend.agents.memory_manager import MemoryManager
from backend.services.llm_client import BaseLLMClient, LLMResponseValidator
from backend.schemas.intent_schema import IntentClassification
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class MemoryExtraction(BaseModel):
    extracted_memories: List[Dict[str, Any]] = Field(
        description="List of extracted memories with 'content', 'category', and 'scope' keys. Valid scopes: user_profile, session, episodic, behavioral"
    )

class MemoryService:
    def __init__(self, memory_manager: MemoryManager, llm_client: BaseLLMClient):
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.validator = LLMResponseValidator(llm_client)

    async def extract_and_store_memories(self, user_id: UUID, session_id: UUID, user_message: str, assistant_response: str) -> None:
        """
        Analyze the conversation turn and extract useful memories using the LLM.
        """
        system_prompt = """
You are the Memory Extraction agent for DailyPlanner AI.
Your job is to analyze the user's message and the assistant's response to extract useful facts, preferences, or observations about the user.

Categories of scopes you can extract:
- user_profile: Static preferences (e.g., "I am a morning person", "I have ADHD").
- behavioral: Observed patterns (e.g., "User tends to push tasks to the weekend").
- episodic: Specific events or context (e.g., "User is preparing for a marathon next month").
- session: Temporary context for the current session (e.g., "User is currently looking for cheap flights").

Only extract a memory if it's explicitly stated or strongly implied and will be useful for future planning. If nothing is worth remembering, return an empty array.

Return a JSON object:
{
  "extracted_memories": [
    {
      "content": "the memory text",
      "category": "preference|event|pattern|context",
      "scope": "user_profile|session|episodic|behavioral"
    }
  ]
}
"""
        prompt = f"User: {user_message}\nAssistant: {assistant_response}\n\nExtract memories:"
        
        try:
            extraction = await self.validator.generate_and_parse(
                system_prompt=system_prompt,
                user_prompt=prompt,
                model_cls=MemoryExtraction
            )
            
            for mem in extraction.extracted_memories:
                await self.memory_manager.add_memory(
                    user_id=user_id,
                    scope=mem.get("scope", "session"),
                    content=mem.get("content", ""),
                    session_id=session_id if mem.get("scope") == "session" else None,
                    category=mem.get("category"),
                    source="ai_inference"
                )
        except Exception as e:
            logger.error(f"Failed to extract memories: {e}")

    async def consolidate_session_memories(self, user_id: UUID, session_id: UUID) -> None:
        """
        End of session background task to review session memories and promote them 
        to episodic or behavioral if they are useful long-term, then deactivate the session memories.
        """
        session_memories = await self.memory_manager.get_memories(user_id, scope="session", session_id=session_id)
        if not session_memories:
            return
            
        memories_text = "\n".join([f"- {m.content}" for m in session_memories])
        
        system_prompt = """
You are the Memory Consolidation agent for DailyPlanner AI.
Below are short-term session memories from a recent conversation. 
Decide which of these represent long-term facts, preferences, or ongoing episodes that should be retained permanently.

Return a JSON object matching this schema:
{
  "extracted_memories": [
    {
      "content": "the memory text",
      "category": "preference|event|pattern",
      "scope": "user_profile|episodic|behavioral"
    }
  ]
}
"""
        try:
            extraction = await self.validator.generate_and_parse(
                system_prompt=system_prompt,
                user_prompt=f"Session Memories:\n{memories_text}",
                model_cls=MemoryExtraction
            )
            
            for mem in extraction.extracted_memories:
                await self.memory_manager.add_memory(
                    user_id=user_id,
                    scope=mem.get("scope", "episodic"),
                    content=mem.get("content", ""),
                    category=mem.get("category"),
                    source="consolidation"
                )
                
            # Deactivate original session memories
            for m in session_memories:
                m.is_active = 0
            await self.memory_manager.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to consolidate memories: {e}")
