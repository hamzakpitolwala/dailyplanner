import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.core.oauth2 import get_current_user
from backend.db.models.core import User
from backend.db.models.ai_engine import AIRecommendation, RecommendationOutcome
from backend.schemas.ai_engine_schema import AIRecommendationResponse, AIRecommendationUpdate, RecommendationOutcomeResponse
from backend.services.pattern_scanner import PatternScannerService
from backend.agents.recommendation_agent import RecommendationAgent
from backend.services.ai_engine_service import AIEngineService
from backend.api.deps import get_ai_engine_service, get_recommendation_agent
from backend.core.limiter import limiter
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai/recommendations",
    tags=["ai_recommendations"],
    responses={401: {"description": "Not authenticated"}},
)

@router.post("/generate", response_model=List[AIRecommendationResponse])
@limiter.limit("10/5minute")
async def generate_recommendations(
    request: Request,
    period_days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agent: RecommendationAgent = Depends(get_recommendation_agent),
):
    """Trigger pattern scanning and LLM recommendation generation."""
    logger.info(f"Generating recommendations for user {current_user.id}")
    
    # 1. Run pattern scanning
    scanner = PatternScannerService(db)
    patterns = await scanner.scan(user_id=str(current_user.id), period_days=period_days)
    
    if not patterns:
        logger.info("No patterns found, returning empty list.")
        return []

    # 2. Call RecommendationAgent (LLM)
    # Fetch profile from DB to avoid lazy-loading MissingGreenlet error
    from backend.db.models.core import UserProfile
    profile_result = await db.execute(select(UserProfile).where(UserProfile.user_id == str(current_user.id)))
    user_profile = profile_result.scalar_one_or_none()
    
    profile = {"goals": user_profile.goals if user_profile else "productivity"}
    history = {"recent_completion_rate": "75%"}
    
    llm_recs = await agent.generate_recommendations(profile, history, patterns)
    
    # 3. Save pending recommendations to DB
    saved_recs = []
    for lr in llm_recs:
        new_rec = AIRecommendation(
            user_id=current_user.id,
            kind=lr.kind,
            scope=lr.scope,
            target_template_id=lr.target.get("template_id"),
            target_daily_planner_id=lr.target.get("daily_planner_id"),
            target_activity_id=lr.target.get("activity_id"),
            payload=lr.payload,
            title=lr.title,
            explanation=lr.explanation,
            status="pending"
        )
        db.add(new_rec)
        saved_recs.append(new_rec)
        
    await db.commit()
    
    if saved_recs:
        rec_ids = [str(r.id) for r in saved_recs]
        result = await db.execute(select(AIRecommendation).where(AIRecommendation.id.in_(rec_ids)))
        saved_recs = list(result.scalars().all())
        
    logger.info(f"Generated {len(saved_recs)} pending recommendations")
    return saved_recs


@router.get("", response_model=List[AIRecommendationResponse])
async def get_recommendations(
    status: Optional[str] = "pending",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recommendations for the current user."""
    query = select(AIRecommendation).where(AIRecommendation.user_id == current_user.id)
    if status:
        query = query.where(AIRecommendation.status == status)
        
    result = await db.execute(query)
    recs = result.scalars().all()
    return recs


@router.post("/{rec_id}/decision", response_model=RecommendationOutcomeResponse)
@limiter.limit("10/5minute")
async def process_decision(
    request: Request,
    rec_id: UUID,
    decision_in: AIRecommendationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_engine_service: AIEngineService = Depends(get_ai_engine_service),
):
    """Process user decision (accept/reject/ignore) for a recommendation."""
    logger.info(f"Processing decision {decision_in.decision} for recommendation {rec_id}")
    
    # Verify ownership
    result = await db.execute(
        select(AIRecommendation).where(
            AIRecommendation.id == str(rec_id),
            AIRecommendation.user_id == str(current_user.id)
        )
    )
    recommendation = result.scalar_one_or_none()
    
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    if recommendation.status != "pending":
        raise HTTPException(status_code=400, detail="Recommendation is already processed")

    if decision_in.decision in ["rejected", "ignored"]:
        recommendation.status = decision_in.decision
        outcome = RecommendationOutcome(
            recommendation_id=str(recommendation.id),
            user_id=str(current_user.id),
            decision=decision_in.decision
        )
        db.add(outcome)
        await db.commit()
        await db.refresh(outcome)
        return outcome
        
    elif decision_in.decision == "accepted":
        outcome = await ai_engine_service.apply_recommendation(
            user_id=current_user.id,
            recommendation=recommendation,
            user_overrides=decision_in.payload
        )
        return outcome
    
    raise HTTPException(status_code=400, detail="Invalid decision")
