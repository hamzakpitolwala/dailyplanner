from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import List, Literal, Optional


# ---------------------------------------------------------------------------
# AI User Profile Schemas
# ---------------------------------------------------------------------------

class AIUserProfileBase(BaseModel):
    """Aiuserprofilebase."""
    personality_type: str | None = Field(default=None, max_length=50)
    productivity_velocity: float = Field(default=1.0)
    ai_inferred_traits: dict | None = None


class AIUserProfileResponse(AIUserProfileBase):
    """Aiuserprofileresponse."""
    id: UUID
    user_id: UUID
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# AI Recommendation Schemas
# ---------------------------------------------------------------------------

class AIRecommendationBase(BaseModel):
    """Airecommendationbase."""
    kind: str = Field(max_length=50) # e.g. move_activity_time
    scope: str = Field(max_length=50) # template | daily_instance | activity | global
    
    target_template_id: UUID | None = None
    target_daily_planner_id: UUID | None = None
    target_activity_id: UUID | None = None
    
    payload: dict = Field(default_factory=dict)
    title: str = Field(max_length=255)
    explanation: str | None = None
    status: str = Field(default="pending", max_length=20)
    source_period_start: str | None = None
    source_period_end: str | None = None


class AIRecommendationCreate(AIRecommendationBase):
    """Airecommendationcreate."""
    pass


class AIRecommendationUpdate(BaseModel):
    """Airecommendationupdate."""
    decision: Literal["accepted", "rejected", "ignored"]
    payload: dict | None = None  # user can optionally tweak the payload before accepting


class AIRecommendationResponse(AIRecommendationBase):
    """Airecommendationresponse."""
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationOutcomeBase(BaseModel):
    """Recommendationoutcomebase."""
    recommendation_id: UUID
    decision: str = Field(max_length=20)
    applied_change_ref: dict | None = None


class RecommendationOutcomeResponse(RecommendationOutcomeBase):
    """Recommendationoutcomeresponse."""
    id: UUID
    user_id: UUID
    decided_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Starter Planner Schemas
# ---------------------------------------------------------------------------

class StarterActivity(BaseModel):
    """Starteractivity."""
    title: str
    category: Optional[str] = None
    start_time: str  # "HH:MM" 24h
    end_time: str    # "HH:MM"
    priority: Literal["low", "medium", "high"] = "medium"
    type: Literal["focus", "admin", "break", "health", "social"] = "focus"
    notes: Optional[str] = None


class StarterPlanner(BaseModel):
    """Starterplanner."""
    template_name: str
    description: Optional[str] = None
    timezone: str
    day_type: Literal["weekday", "weekend", "generic"] = "generic"
    activities: List[StarterActivity]


# ---------------------------------------------------------------------------
# Daily/Weekly Summary Schemas
# ---------------------------------------------------------------------------

class InsightItem(BaseModel):
    """Insightitem."""
    title: str
    detail: str


class SuggestedChange(BaseModel):
    """Suggestedchange."""
    title: str
    description: str
    confidence: float = Field(ge=0, le=1)


class PlannerSummary(BaseModel):
    """Plannersummary."""
    period_type: Literal["day", "week"]
    period_start: str  # ISO date
    period_end: str    # ISO date
    summary_text: str
    wins: List[InsightItem] = Field(default_factory=list)
    issues: List[InsightItem] = Field(default_factory=list)
    suggestions: List[SuggestedChange] = Field(default_factory=list)


class PlannerSummaryResponse(PlannerSummary):
    """Plannersummaryresponse."""
    id: Optional[UUID] = None # None for transient daily summaries
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Conversational AI Schemas
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    """Chatmessage."""
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Chatrequest."""
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    """Chatresponse."""
    reply: str
    structuredType: Optional[str] = None
    structuredData: Optional[dict] = None
