from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class AgentChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None

class AgentChatResponse(BaseModel):
    workflow_id: UUID
    conversation_id: UUID
    status: str # "completed", "waiting_for_user", "proposed"
    message: str # the human readable answer
    tool_calls: Optional[List[Dict[str, Any]]] = None # for frontend to show "proposed" action
    extra_data: Optional[Dict[str, Any]] = None

class AgentApprovalRequest(BaseModel):
    workflow_id: UUID
    approved: bool
    overrides: Optional[Dict[str, Any]] = None

class ConversationSessionOut(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime

class ConversationMessageOut(BaseModel):
    id: UUID
    role: str
    content: Dict[str, Any]
    created_at: datetime
