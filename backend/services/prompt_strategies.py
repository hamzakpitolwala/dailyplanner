import abc
from typing import Any, List
from backend.db.models.core import UserProfile, FixedBlock

class PromptStrategy(abc.ABC):
    """Promptstrategy."""
    @property
    @abc.abstractmethod
    def system_prompt(self) -> str:
        """System prompt."""
        pass
        
    @abc.abstractmethod
    def build_user_prompt(self, **kwargs) -> str:
        """Build user prompt."""
        pass


class StarterPlanPromptStrategy(PromptStrategy):
    """Starterplanpromptstrategy."""
    @property
    def system_prompt(self) -> str:
        """System prompt."""
        return """You are an assistant that designs a structured daily planner template.
You MUST respond with a single JSON object that matches this schema:

{
  "template_name": "string",
  "description": "string",
  "timezone": "string (IANA, e.g. Asia/Kolkata)",
  "day_type": "weekday | weekend | generic",
  "activities": [
    {
      "title": "string",
      "category": "string or null",
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "priority": "low | medium | high",
      "type": "focus | admin | break | health | social",
      "notes": "string or null"
    }
  ]
}

Do NOT include any explanation or extra text. Output JSON only. No markdown formatting.
"""

    def build_user_prompt(
        self, 
        profile: UserProfile, 
        fixed_blocks: List[FixedBlock], 
        calendar_events: List[Any], 
        day_type: str = "generic",
        extra_prompt: str = ""
    ) -> str:
        """Build user prompt."""
        blocks_text = "\n".join([f"- {b.name}: {b.start_time}-{b.end_time} on days {b.days_of_week}" for b in fixed_blocks])
        events_text = "\n".join([f"- {e.summary}: {e.start_time} to {e.end_time}" for e in calendar_events]) if calendar_events else "None"
        
        return f"""
User profile:
- Goals: {profile.goals}
- Focus times: {profile.focus_times}
- Disruptions: {profile.typical_disruptions}
- Structure preference: {profile.structure_preference}
- AI guidance preference: {profile.ai_guidance_level}

Fixed blocks:
{blocks_text or "None"}

Today's calendar events:
{events_text}

Request: Create a starter plan for a {day_type} day.
{("Additional User Instruction: " + extra_prompt) if extra_prompt else ""}

Constraints:
- Respect fixed blocks (do not schedule conflicting tasks).
- Create a realistic day with breaks.
- Focus more time on the main goal.
"""


class WeeklySummaryPromptStrategy(PromptStrategy):
    """Weeklysummarypromptstrategy."""
    @property
    def system_prompt(self) -> str:
        """System prompt."""
        return """You are an assistant that summarizes planner activity performance.
You MUST respond with a single JSON object that matches this schema:

{
  "period_type": "day | week",
  "period_start": "YYYY-MM-DD",
  "period_end": "YYYY-MM-DD",
  "summary_text": "string",
  "wins": [
    {"title": "string", "detail": "string"}
  ],
  "issues": [
    {"title": "string", "detail": "string"}
  ],
  "suggestions": [
    {"title": "string", "description": "string", "confidence": 0.0 to 1.0 float}
  ]
}

Do NOT include any explanation or extra text. Output JSON only. No markdown formatting.
"""

    def build_user_prompt(self, period_start: str, period_end: str, period_type: str, completed_tasks: int, missed_tasks: int, partial_tasks: int, reschedule_count: int, extra_prompt: str = "") -> str:
        """Build user prompt."""
        return f"""
Summarize the {period_type} from {period_start} to {period_end}.

Metrics:
- Completed tasks: {completed_tasks}
- Missed tasks: {missed_tasks}
- Partial/Rescheduled tasks: {partial_tasks + reschedule_count}
{("Additional User Instruction: " + extra_prompt) if extra_prompt else ""}

Please provide a summary, identifying key wins (if completed tasks are high), issues (if missed tasks are high), and practical suggestions to improve.
"""
