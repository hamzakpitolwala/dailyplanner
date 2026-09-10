from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from backend.api.deps import get_ai_engine_service, get_user_service, get_fixed_block_repository, get_task_service, get_chat_agent
from backend.services.ai_engine_service import AIEngineService
from backend.services.user_service import UserService
from backend.services.task_service import TaskService
from backend.db.repositories.fixed_block import FixedBlockRepository
from backend.schemas.ai_engine_schema import StarterPlanner, PlannerSummaryResponse, ChatRequest, ChatResponse
from backend.api.auth_api import get_current_user
from backend.agents.chat_agent import PersonalizedChatAgent
from backend.core.limiter import limiter
from fastapi import Request

router = APIRouter(prefix="/ai", tags=["AI Engine"])

class StarterPlanRequest(BaseModel):
    """Starterplanrequest."""
    day_type: str = "generic"
    extra_prompt: str = ""

@router.post("/generate-starter-plan", response_model=StarterPlanner)
@limiter.limit("10/5minute")
async def generate_starter_plan(
    request: Request,
    req: StarterPlanRequest,
    current_user = Depends(get_current_user),
    ai_service: AIEngineService = Depends(get_ai_engine_service),
    user_service: UserService = Depends(get_user_service),
    fixed_block_repo: FixedBlockRepository = Depends(get_fixed_block_repository),
):
    """Generate starter plan."""
    profile = await user_service.get_user_profile(current_user.id)
    if not profile:
        raise HTTPException(status_code=400, detail="User profile not found. Please complete onboarding.")
    
    fixed_blocks = await fixed_block_repo.list_fixed_blocks(current_user.id)
    # For now calendar events are empty until we integrate daily sync in this layer
    calendar_events = [] 

    return await ai_service.generate_starter_plan(
        user_profile=profile,
        fixed_blocks=fixed_blocks,
        calendar_events=calendar_events,
        day_type=req.day_type,
        extra_prompt=req.extra_prompt,
    )

class SummaryRequest(BaseModel):
    """Summaryrequest."""
    period_type: str = "day" # or "week"
    period_start: str # YYYY-MM-DD
    period_end: str # YYYY-MM-DD
    extra_prompt: str = ""

@router.post("/daily-summary", response_model=PlannerSummaryResponse)
@limiter.limit("10/5minute")
async def generate_summary(
    request: Request,
    req: SummaryRequest,
    current_user = Depends(get_current_user),
    ai_service: AIEngineService = Depends(get_ai_engine_service),
):
    """Generate summary."""
    return await ai_service.generate_summary(
        user_id=current_user.id,
        period_start=req.period_start,
        period_end=req.period_end,
        period_type=req.period_type,
        extra_prompt=req.extra_prompt,
    )

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/5minute")
async def chat(
    request: Request,
    req: ChatRequest,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    task_service: TaskService = Depends(get_task_service),
    fixed_block_repo: FixedBlockRepository = Depends(get_fixed_block_repository),
    chat_agent: PersonalizedChatAgent = Depends(get_chat_agent),
):
    """Chat."""
    reply, s_type, s_data = await chat_agent.chat(
        user_id=current_user.id,
        messages=req.messages,
        user_service=user_service,
        task_service=task_service,
        fixed_block_repo=fixed_block_repo,
    )
    return ChatResponse(reply=reply, structuredType=s_type, structuredData=s_data)
