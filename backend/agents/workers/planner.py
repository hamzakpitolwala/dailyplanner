import json
import logging
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone

from backend.agents.workers.base import BaseWorker
from backend.services.llm_client import BaseLLMClient, LLMResponseValidator
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ToolCall(BaseModel):
    tool_name: str = Field(description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(description="Arguments for the tool")
    explanation: str = Field(description="Explanation of what this tool call will do to show the user")

class PlannerChangeWorker(BaseWorker):
    def __init__(self, llm_client: BaseLLMClient):
        super().__init__(llm_client)
        self.allowed_tools = [
            "create_task", "update_task", "delete_task", "complete_task",
            "move_task", "reschedule_task", "add_subtask",
            "apply_template", "list_templates", "create_template", "add_task_to_template",
            "read_task_in_template", "update_task_in_template", "delete_task_from_template"
        ]
        self.validator = LLMResponseValidator(llm_client)

    async def process(self, user_id: UUID, message: str, context: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Process a planner change request."""
        
        # Fetch active template name
        active_template_name = "None"
        try:
            from backend.db.database import SessionLocal
            from sqlalchemy import select
            from backend.db.models.core import UserProfile
            from backend.db.models.templates import PlannerTemplate
            async with SessionLocal() as db:
                result = await db.execute(select(UserProfile).filter(UserProfile.user_id == str(user_id)))
                profile = result.scalars().first()
                if profile and profile.active_planner_id:
                    result_tmpl = await db.execute(select(PlannerTemplate).filter(PlannerTemplate.id == str(profile.active_planner_id)))
                    tmpl = result_tmpl.scalars().first()
                    if tmpl:
                        active_template_name = tmpl.name
        except Exception as e:
            logger.error(f"Error fetching active template: {e}")

        # Get compact tool descriptions (not full JSON schemas)
        tool_descriptions = await self.get_tool_schemas()
        
        # Build a concise context summary instead of dumping raw JSON
        context_summary = self._build_context_summary(context)
        
        system_prompt = f"""You are a planner assistant. Pick ONE tool to fulfill the user's request.

User ID: {user_id}
Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
Active/Current Template: {active_template_name}

CRITICAL RULES FOR TEMPLATE TASKS:
1. If the user only specifies a task name (e.g. "update read books") for a template CRUD action, ask for the template name using a clarifying response if it's not obvious.
2. If the user says "current template" or "active template", use the Active/Current Template provided above.
3. If the user specifies "all tasks", use `affect_all=True` in the `update_task_in_template` or `delete_task_from_template` tool to affect all tasks in the given template. NEVER use `affect_all` with normal task actions like `complete_task`.
4. If multiple tasks have the same name in a template, verify the time by passing `target_time` to disambiguate.

CRITICAL RULES FOR DAILY PLANNER TASKS:
1. DO NOT silently delete tasks from previous days (historical data). If the user asks to delete a past task, explain that deleting historical data impacts their analytics and AI suggestions, and ask for explicit re-confirmation before proceeding.

Tools (* = required param, ? = optional):
{tool_descriptions}

{context_summary}

Reply with ONLY this JSON:
{{"tool_name": "...", "arguments": {{"user_id": "{user_id}", ...}}, "explanation": "..."}}"""
        
        try:
            tool_call = await self.validator.generate_and_parse(
                system_prompt=system_prompt,
                user_prompt=message,
                model_cls=ToolCall
            )
            
            return {
                "status": "proposed",
                "tool_name": tool_call.tool_name,
                "arguments": tool_call.arguments,
                "explanation": tool_call.explanation,
                "requires_confirmation": True
            }
            
        except Exception as e:
            logger.error(f"PlannerChangeWorker failed: {e}")
            return {"error": str(e)}

    def _build_context_summary(self, context: Dict[str, Any]) -> str:
        """Build a concise context string instead of dumping raw JSON."""
        parts = []
        
        # Memories
        memories = context.get("memories", "")
        if memories and memories != "No prior memories found.":
            # Truncate to first 500 chars
            parts.append(f"User info: {memories[:500]}")
        
        # Templates
        templates = context.get("available_templates", [])
        if templates:
            tmpl_lines = [f"  {t['id']}: {t['name']}" for t in templates[:5]]
            parts.append("Templates:\n" + "\n".join(tmpl_lines))
        
        return "\n".join(parts) if parts else ""
