from datetime import datetime, time
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Template Task Schemas
# ---------------------------------------------------------------------------

class TemplateTaskBase(BaseModel):
    """Templatetaskbase."""
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: int = Field(default=1, ge=1)
    category_label: str | None = Field(default=None, max_length=50)
    relative_day_offset: int = 0
    target_time: time | None = Field(default=None)
    duration_minutes: int = Field(default=60)
    checklist: list[dict] = Field(default_factory=list)
    subtasks: list[dict] = Field(default_factory=list)
    requires_reason: bool = False
    allows_alternate: bool = False


class TemplateTaskCreate(TemplateTaskBase):
    """Templatetaskcreate."""
    pass


class TemplateTaskUpdate(BaseModel):
    """Templatetaskupdate."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    priority: int | None = Field(default=None, ge=1)
    category_label: str | None = Field(default=None, max_length=50)
    relative_day_offset: int | None = None
    target_time: time | None = Field(default=None)
    duration_minutes: int | None = None
    checklist: list[dict] | None = None
    subtasks: list[dict] | None = None
    requires_reason: bool | None = None
    allows_alternate: bool | None = None


class TemplateTaskResponse(TemplateTaskBase):
    """Templatetaskresponse."""
    id: UUID
    template_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Planner Template Schemas
# ---------------------------------------------------------------------------

class PlannerTemplateBase(BaseModel):
    """Plannertemplatebase."""
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class PlannerTemplateCreate(PlannerTemplateBase):
    """Plannertemplatecreate."""
    template_tasks: list[TemplateTaskCreate] = Field(default_factory=list)


class PlannerTemplateUpdate(BaseModel):
    """Plannertemplateupdate."""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class PlannerTemplateResponse(PlannerTemplateBase):
    """Plannertemplateresponse."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    template_tasks: list[TemplateTaskResponse] = []
    task_count: int = 0

    model_config = {"from_attributes": True}
