import logging
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from backend.agents.workers.base import BaseWorker
from backend.services.llm_client import BaseLLMClient

logger = logging.getLogger(__name__)

class ConversationWorker(BaseWorker):
    """Conversationworker."""
    def __init__(self, llm_client: BaseLLMClient):
        """  init  ."""
        super().__init__(llm_client)
        self.allowed_tools = [] # No tools for general conversation

    async def process(self, user_id: UUID, message: str, context: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Process a conversation or clarification request."""
        
        system_prompt = f"""
You are the Conversation Worker for DailyPlanner AI.
Your job is to provide a friendly, helpful, and motivating response to the user.
Current time: {datetime.now(timezone.utc).isoformat()}

Context provided:
{context}

Intent details:
{intent}

If the intent type is 'clarification', you MUST ask the user the clarification question provided in the intent details.
Otherwise, respond naturally to the user's message.
"""
        try:
            final_response = await self.llm_client.chat(system_prompt, message)
            
            return {
                "status": "completed",
                "explanation": final_response,
                "requires_confirmation": False
            }
            
        except Exception as e:
            logger.error(f"ConversationWorker failed: {e}")
            return {"error": str(e)}
