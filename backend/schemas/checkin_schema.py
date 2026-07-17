"""Pydantic schemas for the check-in flow."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class CheckinStatus(str, Enum):
    """Allowed statuses when checking in on an activity."""

    done = "done"
    not_done = "not_done"
    partial = "partial"
    rescheduled = "rescheduled"


class ReasonCode(str, Enum):
    """Predefined reason codes for why an activity was missed."""

    too_busy = "too_busy"
    forgot = "forgot"
    not_feeling_well = "not_feeling_well"
    schedule_conflict = "schedule_conflict"
    low_priority = "low_priority"
    other = "other"


# ---------------------------------------------------------------------------
# Nested create/response schemas
# ---------------------------------------------------------------------------


class MissedReasonCreate(BaseModel):
    reason_code: ReasonCode
    free_text: str | None = Field(default=None, max_length=500)


class MissedReasonResponse(BaseModel):
    id: int
    checkin_id: int
    reason_code: str
    free_text: str | None = None

    model_config = {"from_attributes": True}


class AlternateActivityCreate(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    category: str | None = Field(default=None, max_length=80)


class AlternateActivityResponse(BaseModel):
    id: int
    checkin_id: int
    description: str
    category: str | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Check-in create / response
# ---------------------------------------------------------------------------


class CheckinCreate(BaseModel):
    """Payload to create a check-in on an activity.

    Conditional fields:
    - ``missed_reason`` is relevant only when ``status == not_done``.
    - ``alternate_activity`` is relevant only when ``status == not_done``.

    The *service layer* enforces whether these are required based on the
    activity's ``ActivityPolicy``.
    """

    status: CheckinStatus
    notes: str | None = Field(default=None, max_length=1000)
    missed_reason: MissedReasonCreate | None = None
    alternate_activity: AlternateActivityCreate | None = None

    @model_validator(mode="after")
    def strip_irrelevant_fields(self):
        """Silently drop reason/alternate when the status is not 'not_done'."""
        if self.status != CheckinStatus.not_done:
            self.missed_reason = None
            self.alternate_activity = None
        return self


class CheckinResponse(BaseModel):
    id: int
    activity_id: int
    user_id: int
    status: str
    notes: str | None = None
    checked_in_at: datetime
    missed_reason: MissedReasonResponse | None = None
    alternate_activity: AlternateActivityResponse | None = None

    model_config = {"from_attributes": True}
