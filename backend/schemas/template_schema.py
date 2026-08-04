from datetime import datetime, time
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Template Task Schemas
# ---------------------------------------------------------------------------

class TemplateTaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: int = Field(default=1, ge=1)
    category_label: str | None = Field(default=None, max_length=50)
    relative_day_offset: int = 0
    target_time: str | None = Field(default=None, max_length=8)

    @field_validator('target_time', mode='before')
    @classmethod
    def validate_target_time(cls, v):
        if isinstance(v, time):
            return v.strftime("%H:%M:%S")
        return v
    duration_minutes: int = Field(default=60)
    checklist: list[dict] = Field(default_factory=list)
    subtasks: list[dict] = Field(default_factory=list)


class TemplateTaskCreate(TemplateTaskBase):
    pass


class TemplateTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    priority: int | None = Field(default=None, ge=1)
    category_label: str | None = Field(default=None, max_length=50)
    relative_day_offset: int | None = None
    target_time: str | None = Field(default=None, max_length=8)
    duration_minutes: int | None = None
    checklist: list[dict] | None = None
    subtasks: list[dict] | None = None


class TemplateTaskResponse(TemplateTaskBase):
    id: UUID
    template_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Planner Template Schemas
# ---------------------------------------------------------------------------

class PlannerTemplateBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class PlannerTemplateCreate(PlannerTemplateBase):
    template_tasks: list[TemplateTaskCreate] = Field(default_factory=list)


class PlannerTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class PlannerTemplateResponse(PlannerTemplateBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    template_tasks: list[TemplateTaskResponse] = []

    model_config = {"from_attributes": True}