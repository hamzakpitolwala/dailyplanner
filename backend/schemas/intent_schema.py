from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field

class Intent(BaseModel):
    """Intent."""
    type: Literal["planner_change", "insight", "conversation", "clarification", "unsupported"] = Field(
        description="The category of the intent."
    )
    target_description: Optional[str] = Field(
        default=None, 
        description="Description of what the user wants to target (e.g. 'gym task', 'project report')."
    )
    target_operation: Optional[str] = Field(
        default=None,
        description="Operation to perform (e.g. 'move', 'create', 'delete', 'summary')."
    )
    target_date: Optional[str] = Field(
        default=None,
        description="Relevant date or timeframe (e.g. 'tomorrow', 'next week')."
    )
    requires_confirmation: bool = Field(
        default=False,
        description="True if this intent modifies data and requires user confirmation."
    )
    requires_clarification: bool = Field(
        default=False,
        description="True if the request is ambiguous."
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="Question to ask the user if clarification is needed."
    )

class IntentClassification(BaseModel):
    """Intentclassification."""
    intents: List[Intent] = Field(description="List of identified intents from the user's message.")
