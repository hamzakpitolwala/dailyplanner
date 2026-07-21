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
# Task Schemas
# ---------------------------------------------------------------------------

class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: int = Field(default=1, ge=1)
    status: str = Field(default="pending", max_length=20)
    checklist: list[dict] = Field(default_factory=list)
    source_template_name: str | None = Field(default=None, max_length=100)
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    category_id: UUID | None = None


class TaskUpdate(BaseModel):
    category_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    priority: int | None = Field(default=None, ge=1)
    status: str | None = Field(default=None, max_length=20)
    checklist: list[dict] | None = None
    source_template_name: str | None = Field(default=None, max_length=100)
    due_date: datetime | None = None
    completed_at: datetime | None = None


class TaskResponse(TaskBase):
    id: UUID
    user_id: UUID
    category_id: UUID | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}