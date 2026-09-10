import time
import json
import logging
import re
from typing import List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone

from backend.schemas.ai_engine_schema import ChatMessage
from backend.services.llm_client import OllamaClient
from backend.services.user_service import UserService
from backend.services.task_service import TaskService
from backend.db.repositories.fixed_block import FixedBlockRepository

logger = logging.getLogger(__name__)

# Global cache to prevent repeated DB hits
# Format: { user_id_str: { "context_str": "...", "expires_at": float } }
_context_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

class PersonalizedChatAgent:
    """Personalizedchatagent."""
    def __init__(self):
        """  init  ."""
        self.llm_client = OllamaClient()

    async def _fetch_context_str(
        self, 
        user_id: UUID, 
        user_service: UserService, 
        task_service: TaskService, 
        fixed_block_repo: FixedBlockRepository
    ) -> str:
        # Fetch profile
        """ fetch context str."""
        profile = await user_service.get_user_profile(user_id)
        profile_str = ""
        if profile:
            profile_str = f"Goals/Focus: {profile.goals}\nFocus Times: {profile.focus_times}\nStructure Preference: {profile.structure_preference}\n"
            
        # Fetch fixed blocks
        blocks = await fixed_block_repo.list_fixed_blocks(user_id)
        blocks_str = "\n".join([f"- {b.name} ({b.start_time}-{b.end_time})" for b in blocks])
        
        # Fetch today's tasks
        now = datetime.now(timezone.utc)
        target_date_str = now.strftime("%Y-%m-%d")
        
        tasks = await task_service.list_tasks(user_id, target_date=target_date_str)
        tasks_str = ""
        for t in tasks:
            status = "completed" if t.status == "completed" else "pending"
            tasks_str += f"- {t.title} ({t.start_time}-{t.due_date}) [{status}]\n"
            
        context_str = (
            f"User Profile:\n{profile_str}\n"
            f"Fixed Blocks:\n{blocks_str}\n\n"
            f"Today's Schedule ({target_date_str}):\n{tasks_str}"
        )
        return context_str

    async def get_or_fetch_context(
        self, 
        user_id: UUID, 
        user_service: UserService, 
        task_service: TaskService, 
        fixed_block_repo: FixedBlockRepository
    ) -> str:
        """Get or fetch context."""
        uid_str = str(user_id)
        now = time.time()
        
        # Check cache
        if uid_str in _context_cache:
            cache_entry = _context_cache[uid_str]
            if now < cache_entry["expires_at"]:
                logger.debug(f"Using cached context for user {uid_str}")
                return cache_entry["context_str"]
                
        # Cache miss or expired, fetch again
        logger.info(f"Fetching fresh DB context for user {uid_str}")
        context_str = await self._fetch_context_str(user_id, user_service, task_service, fixed_block_repo)
        
        # Save to cache
        _context_cache[uid_str] = {
            "context_str": context_str,
            "expires_at": now + CACHE_TTL_SECONDS
        }
        
        return context_str

    async def chat(
        self,
        user_id: UUID,
        messages: List[ChatMessage],
        user_service: UserService,
        task_service: TaskService,
        fixed_block_repo: FixedBlockRepository
    ) -> Tuple[str, str | None, dict | None]:
        """Chat."""
        context_str = await self.get_or_fetch_context(user_id, user_service, task_service, fixed_block_repo)
        
        system_prompt = (
            "You are PlannerAI, a highly personalized daily planning assistant. "
            "You help the user manage their tasks, schedule, and life.\n"
            "CRITICAL RULES FOR RESPONDING:\n"
            "1. If the user just wants to chat, provide a conversational reply.\n"
            "2. If the user asks you to generate a schedule, plan, or suggest changes to their daily planner, "
            "you MUST output a JSON block containing the structured data. The JSON block MUST be wrapped in ```json ... ``` tags.\n"
            "For a starter plan, the JSON must look like: {\"structuredType\": \"starter\", \"structuredData\": {\"template_name\": \"...\", \"description\": \"...\", \"activities\": [{\"title\": \"...\", \"start_time\": \"HH:MM\", \"end_time\": \"HH:MM\", \"priority\": \"high\"}]}}\n"
            "You can include conversational text outside the JSON block.\n\n"
            "--- USER CONTEXT ---\n"
            f"{context_str}\n"
            "-------------------\n"
        )
        
        full_prompt = "Conversation History:\n"
        for msg in messages:
            full_prompt += f"{msg.role.upper()}: {msg.content}\n"
            
        full_prompt += "ASSISTANT: "
        
        reply = await self.llm_client.chat(system_prompt, full_prompt)
        
        structured_type = None
        structured_data = None
        
        # Parse for JSON block
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", reply, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                if "structuredType" in parsed and "structuredData" in parsed:
                    structured_type = parsed["structuredType"]
                    structured_data = parsed["structuredData"]
                    # Remove the JSON block from the reply text
                    reply = reply.replace(json_match.group(0), "").strip()
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON block from LLM response")
                
        return reply, structured_type, structured_data
