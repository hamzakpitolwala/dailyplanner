from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# AI User Profile Schemas
# ---------------------------------------------------------------------------

class AIUserProfileBase(BaseModel):
    personality_type: str | None = Field(default=None, max_length=50)
    productivity_velocity: float = Field(default=1.0)
    ai_inferred_traits: dict | None = None


class AIUserProfileResponse(AIUserProfileBase):
    id: UUID
    user_id: UUID
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# AI Recommendation Schemas
# ---------------------------------------------------------------------------

class AIRecommendationBase(BaseModel):
    recommendation_text: str
    rationale: str | None = None
    suggested_changes: dict
    status: str = Field(default="pending", max_length=20)


class AIRecommendationUpdate(BaseModel):
    status: str = Field(max_length=20)  # e.g. "accepted", "dismissed"


class AIRecommendationResponse(AIRecommendationBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}