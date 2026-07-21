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
    source_provider: str = Field(max_length=50)
    external_id: str = Field(max_length=255)
    event_type: str = Field(max_length=50)
    parsed_summary: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    metadata: dict | None = None


class ExternalSyncedEventCreate(ExternalSyncedEventBase):
    pass


class ExternalSyncedEventResponse(ExternalSyncedEventBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}