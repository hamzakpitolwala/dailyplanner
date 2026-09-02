import json
import logging
from typing import List, Optional
from datetime import datetime, timezone

from backend.services.llm_client import BaseLLMClient, LLMResponseValidator
from backend.schemas.intent_schema import IntentClassification, Intent

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, llm_client: BaseLLMClient):
        self.validator = LLMResponseValidator(llm_client)

    async def classify_intent(self, user_message: str) -> IntentClassification:
        system_prompt = f"""
You are the Orchestrator for DailyPlanner AI. Your job is to classify the user's intent based on their message.
The current date and time is {datetime.now(timezone.utc).isoformat()}.

Possible intent types:
1. "planner_change": Create, update, delete, complete, move, or reschedule tasks.
2. "insight": Read-only operations asking for summary, workload, schedule, conflicts, goals, or overdue tasks.
3. "conversation": General chat, advice, motivation, or questions that don't fit the above.
4. "clarification": The request is ambiguous and you need more details.
5. "unsupported": The request cannot be fulfilled by the AI.

If the user asks multiple things, return multiple intents in the 'intents' array.
For 'planner_change', set 'requires_confirmation' to true if it modifies existing data.
If ambiguous, set 'requires_clarification' to true and provide a 'clarification_question'.

You must respond ONLY with valid JSON matching this schema:
{{
  "intents": [
    {{
      "type": "planner_change|insight|conversation|clarification|unsupported",
      "target_description": "optional description",
      "target_operation": "optional operation",
      "target_date": "optional date",
      "requires_confirmation": bool,
      "requires_clarification": bool,
      "clarification_question": "optional string"
    }}
  ]
}}
"""
        try:
            return await self.validator.generate_and_parse(
                system_prompt=system_prompt,
                user_prompt=user_message,
                model_cls=IntentClassification
            )
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Fallback to conversation intent if classification fails
            return IntentClassification(intents=[Intent(type="conversation", requires_clarification=True, clarification_question="I'm sorry, I couldn't understand that. Could you rephrase?")])
