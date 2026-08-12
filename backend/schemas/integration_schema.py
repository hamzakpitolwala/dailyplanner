from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# OAuth Token Schemas
# ---------------------------------------------------------------------------

class UserOAuthTokenBase(BaseModel):
    provider: str = Field(max_length=50)
    scopes: list[str]


class UserOAuthTokenResponse(UserOAuthTokenBase):
    id: UUID
    user_id: UUID
    expires_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# External Synced Event Schemas
# ---------------------------------------------------------------------------

class ExternalSyncedEventBase(BaseModel):
    source_provider: str = Field(default="google", max_length=50)
    external_id: str = Field(max_length=255)
    calendar_id: str = Field(default="primary", max_length=255)
    event_type: str = Field(default="calendar_event", max_length=50)
    parsed_summary: str = Field(default="")
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    status: str = Field(default="confirmed", max_length=50)
    start_time: datetime | None = None
    end_time: datetime | None = None
    raw_payload: dict | None = None
    metadata: dict | None = Field(default=None, validation_alias="extra_metadata", serialization_alias="metadata")

    model_config = {"populate_by_name": True}


class ExternalSyncedEventCreate(ExternalSyncedEventBase):
    pass


class ExternalSyncedEventResponse(ExternalSyncedEventBase):
    id: UUID
    user_id: UUID
    last_synced_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}