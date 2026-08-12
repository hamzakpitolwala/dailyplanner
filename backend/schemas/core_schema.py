from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Category Schemas
# ---------------------------------------------------------------------------

class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color_hex: str = Field(default="#FFFFFF", min_length=7, max_length=7)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color_hex: str | None = Field(default=None, min_length=7, max_length=7)


class CategoryResponse(CategoryBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Subtask Schemas
# ---------------------------------------------------------------------------

class SubtaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    is_completed: bool = False

class SubtaskCreate(SubtaskBase):
    pass

class SubtaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    is_completed: bool | None = None

class SubtaskResponse(SubtaskBase):
    id: UUID
    task_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Task Schemas
# ---------------------------------------------------------------------------

class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: int = Field(default=1, ge=1)
    status: str = Field(default="pending", max_length=20)
    checklist: list[dict] = Field(default_factory=list)
    source_template_id: str | None = Field(default=None, max_length=36)
    source_template_task_id: str | None = Field(default=None, max_length=36)
    source_template_name: str | None = Field(default=None, max_length=255)
    start_time: datetime | None = None
    due_date: datetime | None = None
    requires_reason: bool = False
    allows_alternate: bool = False
    source: str = Field(default="manual", max_length=20)
    external_event_id: UUID | None = None
    visibility: str = Field(default="normal", max_length=20)


class TaskCreate(TaskBase):
    category_id: UUID | None = None
    subtasks: list[SubtaskCreate] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    category_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    priority: int | None = Field(default=None, ge=1)
    status: str | None = Field(default=None, max_length=20)
    checklist: list[dict] | None = None
    source_template_id: str | None = Field(default=None, max_length=36)
    source_template_task_id: str | None = Field(default=None, max_length=36)
    start_time: datetime | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    requires_reason: bool | None = None
    allows_alternate: bool | None = None
    source: str | None = Field(default=None, max_length=20)
    external_event_id: UUID | None = None
    visibility: str | None = Field(default=None, max_length=20)


class TaskResponse(TaskBase):
    id: UUID
    user_id: UUID
    category_id: UUID | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    checkins: list["TaskCheckinResponse"] = Field(default_factory=list)
    subtasks: list["SubtaskResponse"] = Field(default_factory=list)

    model_config = {"from_attributes": True}



# ---------------------------------------------------------------------------
# Check-in Schemas
# ---------------------------------------------------------------------------

class MissedReasonResponse(BaseModel):
    id: UUID
    name: str
    user_id: UUID | None = None

    model_config = {"from_attributes": True}


class AlternateActivityResponse(BaseModel):
    id: UUID
    name: str
    user_id: UUID | None = None

    model_config = {"from_attributes": True}


class TaskCheckinCreate(BaseModel):
    status: str = Field(max_length=20)
    missed_reason_id: UUID | None = None
    alternate_activity_id: UUID | None = None
    notes: str | None = None


class TaskCheckinResponse(BaseModel):
    id: UUID
    task_id: UUID
    status: str
    missed_reason_id: UUID | None = None
    alternate_activity_id: UUID | None = None
    notes: str | None = None
    created_at: datetime
    missed_reason: MissedReasonResponse | None = None
    alternate_activity: AlternateActivityResponse | None = None
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# User Profile Schemas
# ---------------------------------------------------------------------------

class UserProfileBase(BaseModel):
    username: str | None = None
    dob: str | None = None
    gender: str | None = None
    goals: str | None = None
    focus_times: str | None = None
    typical_disruptions: str | None = None
    structure_preference: str | None = None
    ai_guidance_level: str | None = None
    onboarding_completed: bool = False
    personality_type: str | None = None
    productivity_velocity: float = 1.0
    active_planner_id: UUID | None = None
    last_login_date: str | None = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    username: str | None = None
    dob: str | None = None
    gender: str | None = None
    goals: str | None = None
    focus_times: str | None = None
    typical_disruptions: str | None = None
    structure_preference: str | None = None
    ai_guidance_level: str | None = None
    onboarding_completed: bool | None = None
    personality_type: str | None = None
    productivity_velocity: float | None = None
    active_planner_id: UUID | None = None
    last_login_date: str | None = None


class UserProfileResponse(UserProfileBase):
    id: UUID
    user_id: UUID
    updated_at: datetime | None = None
    ai_inferred_traits: dict | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Fixed Block Schemas
# ---------------------------------------------------------------------------

class FixedBlockBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    start_time: str = Field(min_length=5, max_length=5) # HH:MM
    end_time: str = Field(min_length=5, max_length=5)   # HH:MM
    days_of_week: list[int]


class FixedBlockCreate(FixedBlockBase):
    pass


class FixedBlockUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    start_time: str | None = Field(default=None, min_length=5, max_length=5)
    end_time: str | None = Field(default=None, min_length=5, max_length=5)
    days_of_week: list[int] | None = None


class FixedBlockResponse(FixedBlockBase):
    id: UUID
    user_id: UUID

    model_config = {"from_attributes": True}

TaskResponse.model_rebuild()