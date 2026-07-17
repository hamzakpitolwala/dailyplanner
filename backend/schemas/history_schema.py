"""Pydantic schemas for the history and state machine flow."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ActivityStatus(str, Enum):
    """Allowed statuses in the state machine."""
    planned = "planned"
    in_progress = "in_progress"
    partial = "partial"
    done = "done"
    not_done = "not_done"
    rescheduled = "rescheduled"
    cancelled = "cancelled"

class ActionType(str, Enum):
    status_change = "status_change"
    edit = "edit"
    reschedule = "reschedule"
    creation = "creation"

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
    history_event_id: int
    reason_code: str
    free_text: str | None = None

    model_config = {"from_attributes": True}


class AlternateActivityCreate(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    category: str | None = Field(default=None, max_length=80)


class AlternateActivityResponse(BaseModel):
    id: int
    history_event_id: int
    description: str
    category: str | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# History Event create / response
# ---------------------------------------------------------------------------


class HistoryEventCreate(BaseModel):
    """Payload to create a history event (e.g., status change) on an activity.

    Conditional fields:
    - ``missed_reason`` is relevant only when ``new_state == not_done``.
    - ``alternate_activity`` is relevant only when ``new_state == not_done``.
    """

    action_type: ActionType
    new_state: ActivityStatus
    notes: str | None = Field(default=None, max_length=1000)
    target_date: str | None = None  # Used when action_type=status_change and new_state=rescheduled
    missed_reason: MissedReasonCreate | None = None
    alternate_activity: AlternateActivityCreate | None = None

    @model_validator(mode="after")
    def strip_irrelevant_fields(self):
        """Silently drop reason/alternate when the status is not 'not_done'."""
        if self.new_state != ActivityStatus.not_done:
            self.missed_reason = None
            self.alternate_activity = None
        return self


class HistoryEventResponse(BaseModel):
    id: int
    activity_id: int
    user_id: int
    action_type: str
    previous_state: str | None = None
    new_state: str
    notes: str | None = None
    timestamp: datetime
    missed_reason: MissedReasonResponse | None = None
    alternate_activity: AlternateActivityResponse | None = None

    model_config = {"from_attributes": True}
