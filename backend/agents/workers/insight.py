import json
import logging
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone

from backend.agents.workers.base import BaseWorker
from backend.services.llm_client import BaseLLMClient, LLMResponseValidator
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ToolCallInsight(BaseModel):
    tool_name: str = Field(description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(description="Arguments for the tool")

class InsightWorker(BaseWorker):
    def __init__(self, llm_client: BaseLLMClient):
        super().__init__(llm_client)
        self.allowed_tools = [
            "get_tasks", "get_schedule", "get_today_summary",
            "get_overdue_tasks", "find_schedule_conflicts", "get_analytics"
        ]
        self.validator = LLMResponseValidator(llm_client)

    async def process(self, user_id: UUID, message: str, context: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Process an insight/read-only request."""
        
        tool_schemas_json = await self.get_tool_schemas()
        
        # Step 1: Decide which tool to call
        system_prompt_decision = f"""
You are the Insight Worker for DailyPlanner AI. Your job is to select the correct read-only tool to answer the user's question.
Current time: {datetime.now(timezone.utc).isoformat()}
User ID: {user_id}

Available Tools:
{tool_schemas_json}

Context provided:
{json.dumps(context, default=str)}

Respond ONLY with valid JSON matching this schema:
{{
  "tool_name": "name of the tool from the allowed list",
  "arguments": {{
    "arg1": "value",
    "user_id": "{user_id}"
  }}
}}
"""
        try:
            # 1. Decide tool
            tool_call = await self.validator.generate_and_parse(
                system_prompt=system_prompt_decision,
                user_prompt=message,
                model_cls=ToolCallInsight
            )
            
            # 2. Execute tool directly (auto-approved because it's read-only)
            tool_result = await self.execute_tool(tool_call.tool_name, tool_call.arguments)
            
            # 3. Generate natural language response
            system_prompt_summary = f"""
You are the Insight Worker for DailyPlanner AI. 
You have executed the tool '{tool_call.tool_name}' and got the following result:
{json.dumps(tool_result, default=str)}

Based on the original message from the user: "{message}"
Write a friendly, concise, and helpful response.
"""
            final_response = await self.llm_client.chat(system_prompt_summary, "Provide the final answer to the user.")
            
            return {
                "status": "completed",
                "tool_name": tool_call.tool_name,
                "arguments": tool_call.arguments,
                "tool_result": tool_result,
                "explanation": final_response,
                "requires_confirmation": False
            }
            
        except Exception as e:
            logger.error(f"InsightWorker failed: {e}")
            return {"error": str(e)}
