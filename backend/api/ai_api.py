from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from backend.api.deps import get_ai_engine_service, get_user_service, get_fixed_block_repository, get_task_service
from backend.services.ai_engine_service import AIEngineService
from backend.services.user_service import UserService
from backend.services.task_service import TaskService
from backend.db.repositories.fixed_block import FixedBlockRepository
from backend.schemas.ai_engine_schema import StarterPlanner, PlannerSummaryResponse, ChatRequest, ChatResponse
from backend.api.auth_api import get_current_user
from backend.agents.chat_agent import PersonalizedChatAgent

router = APIRouter(prefix="/ai", tags=["AI Engine"])

chat_agent = PersonalizedChatAgent()

class StarterPlanRequest(BaseModel):
    day_type: str = "generic"
    extra_prompt: str = ""

@router.post("/generate-starter-plan", response_model=StarterPlanner)
async def generate_starter_plan(
    req: StarterPlanRequest,
    current_user = Depends(get_current_user),
    ai_service: AIEngineService = Depends(get_ai_engine_service),
    user_service: UserService = Depends(get_user_service),
    fixed_block_repo: FixedBlockRepository = Depends(get_fixed_block_repository),
):
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
    period_type: str = "day" # or "week"
    period_start: str # YYYY-MM-DD
    period_end: str # YYYY-MM-DD
    extra_prompt: str = ""

@router.post("/daily-summary", response_model=PlannerSummaryResponse)
async def generate_summary(
    req: SummaryRequest,
    current_user = Depends(get_current_user),
    ai_service: AIEngineService = Depends(get_ai_engine_service),
):
    return await ai_service.generate_summary(
        user_id=current_user.id,
        period_start=req.period_start,
        period_end=req.period_end,
        period_type=req.period_type,
        extra_prompt=req.extra_prompt,
    )

@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    task_service: TaskService = Depends(get_task_service),
    fixed_block_repo: FixedBlockRepository = Depends(get_fixed_block_repository),
):
    reply, s_type, s_data = await chat_agent.chat(
        user_id=current_user.id,
        messages=req.messages,
        user_service=user_service,
        task_service=task_service,
        fixed_block_repo=fixed_block_repo,
    )
    return ChatResponse(reply=reply, structuredType=s_type, structuredData=s_data)
