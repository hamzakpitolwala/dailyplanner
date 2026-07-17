"""Pydantic schemas for templates."""

from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Activity Templates
# ---------------------------------------------------------------------------

class ActivityTemplateBase(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    category: str | None = Field(default=None, max_length=80)
    start_time: str | None = None
    end_time: str | None = None


class ActivityTemplateCreate(ActivityTemplateBase):
    pass


class ActivityTemplateUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    category: str | None = Field(default=None, max_length=80)
    start_time: str | None = None
    end_time: str | None = None


class ActivityTemplateResponse(ActivityTemplateBase):
    id: int
    planner_template_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Planner Templates
# ---------------------------------------------------------------------------

class PlannerTemplateBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    in_use: bool = False


class PlannerTemplateCreate(PlannerTemplateBase):
    pass


class PlannerTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    in_use: bool | None = None


class PlannerTemplateResponse(PlannerTemplateBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    activity_templates: list[ActivityTemplateResponse] = []

    model_config = {"from_attributes": True}
