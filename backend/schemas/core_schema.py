from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Category Schemas
# ---------------------------------------------------------------------------

class CategoryBase(BaseModel):
    """Categorybase."""
    name: str = Field(min_length=1, max_length=50)
    color_hex: str = Field(default="#FFFFFF", min_length=7, max_length=7)


class CategoryCreate(CategoryBase):
    """Categorycreate."""
    pass


class CategoryUpdate(BaseModel):
    """Categoryupdate."""
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color_hex: str | None = Field(default=None, min_length=7, max_length=7)


class CategoryResponse(CategoryBase):
    """Categoryresponse."""
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Subtask Schemas
# ---------------------------------------------------------------------------

class SubtaskBase(BaseModel):
    """Subtaskbase."""
    title: str = Field(min_length=1, max_length=255)
    is_completed: bool = False

class SubtaskCreate(SubtaskBase):
    """Subtaskcreate."""
    pass

class SubtaskUpdate(BaseModel):
    """Subtaskupdate."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    is_completed: bool | None = None

class SubtaskResponse(SubtaskBase):
    """Subtaskresponse."""
    id: UUID
    task_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Task Schemas
# ---------------------------------------------------------------------------

class TaskBase(BaseModel):
    """Taskbase."""
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
    """Taskcreate."""
    category_id: UUID | None = None
    subtasks: list[SubtaskCreate] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Taskupdate."""
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
    """Taskresponse."""
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
    """Missedreasonresponse."""
    id: UUID
    name: str
    user_id: UUID | None = None

    model_config = {"from_attributes": True}


class AlternateActivityResponse(BaseModel):
    """Alternateactivityresponse."""
    id: UUID
    name: str
    user_id: UUID | None = None

    model_config = {"from_attributes": True}


class TaskCheckinCreate(BaseModel):
    """Taskcheckincreate."""
    status: str = Field(max_length=20)
    missed_reason_id: UUID | None = None
    alternate_activity_id: UUID | None = None
    notes: str | None = None


class TaskCheckinResponse(BaseModel):
    """Taskcheckinresponse."""
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
    """Userprofilebase."""
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
    """Userprofilecreate."""
    pass


class UserProfileUpdate(BaseModel):
    """Userprofileupdate."""
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
    """Userprofileresponse."""
    id: UUID
    user_id: UUID
    updated_at: datetime | None = None
    ai_inferred_traits: dict | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Fixed Block Schemas
# ---------------------------------------------------------------------------

class FixedBlockBase(BaseModel):
    """Fixedblockbase."""
    name: str = Field(min_length=1, max_length=255)
    start_time: str = Field(min_length=5, max_length=5) # HH:MM
    end_time: str = Field(min_length=5, max_length=5)   # HH:MM
    days_of_week: list[int]
    apply_all: bool = True
    template_ids: list[str] = Field(default_factory=list)


class FixedBlockCreate(FixedBlockBase):
    """Fixedblockcreate."""
    pass


class FixedBlockUpdate(BaseModel):
    """Fixedblockupdate."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    start_time: str | None = Field(default=None, min_length=5, max_length=5)
    end_time: str | None = Field(default=None, min_length=5, max_length=5)
    days_of_week: list[int] | None = None
    apply_all: bool | None = None
    template_ids: list[str] | None = None


class FixedBlockResponse(FixedBlockBase):
    """Fixedblockresponse."""
    id: UUID
    user_id: UUID

    model_config = {"from_attributes": True}

TaskResponse.model_rebuild()
