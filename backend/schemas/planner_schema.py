from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, Field, model_validator


class ActivityPolicyBase(BaseModel):
    requires_reason: bool = True
    allows_alternate: bool = True
    monitoring_allowed: bool = False


class ActivityPolicyResponse(ActivityPolicyBase):
    id: int
    activity_id: int

    model_config = {"from_attributes": True}


class ActivityBase(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = None
    category: str | None = Field(default=None, max_length=80)
    start_time: time | None = None
    end_time: time | None = None

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ActivityCreate(ActivityBase):
    policy: ActivityPolicyBase | None = None


class ActivityUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    category: str | None = Field(default=None, max_length=80)
    start_time: time | None = None
    end_time: time | None = None
    status: str | None = Field(default=None, max_length=32)
    policy: ActivityPolicyBase | None = None

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ActivityResponse(ActivityBase):
    id: int
    planner_id: int
    status: str
    carried_over_from_id: int | None = None
    policy: ActivityPolicyResponse | None = None
    history_events: list[HistoryEventResponse] = []

    model_config = {"from_attributes": True}


# Import here to avoid circular imports (HistoryEventResponse references ActivityResponse indirectly)
from backend.schemas.history_schema import HistoryEventResponse  # noqa: E402


class DailyPlannerBase(BaseModel):
    planner_date: date
    title: str = Field(min_length=1, max_length=160)
    notes: str | None = None


class DailyPlannerCreate(DailyPlannerBase):
    pass


class DailyPlannerUpdate(BaseModel):
    planner_date: date | None = None
    title: str | None = Field(default=None, min_length=1, max_length=160)
    notes: str | None = None


class DailyPlannerResponse(DailyPlannerBase):
    id: int
    activities: list[ActivityResponse] = []

    model_config = {"from_attributes": True}
