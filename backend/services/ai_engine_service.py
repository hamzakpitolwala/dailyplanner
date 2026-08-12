from uuid import UUID
from datetime import datetime, timezone

from backend.db.models.ai_engine import AIRecommendation, AIUserProfile, AISummary, RecommendationOutcome
from backend.schemas.ai_engine_schema import AIRecommendationUpdate, StarterPlanner, PlannerSummaryResponse
from backend.db.repositories.ai_record import (
    AIUserProfileRepository,
    AIRecommendationRepository,
    AISummaryRepository,
    RecommendationOutcomeRepository,
)
from backend.services.llm_client import BaseLLMClient, LLMResponseValidator
from backend.services.prompt_strategies import StarterPlanPromptStrategy, WeeklySummaryPromptStrategy
from backend.db.models.core import UserProfile, FixedBlock
from backend.services.task_service import TaskService
import json


class AIEngineService:
    """Service layer for managing AI features and interactions."""

    def __init__(
        self,
        ai_profile_repo: AIUserProfileRepository,
        ai_recommendation_repo: AIRecommendationRepository,
        ai_summary_repo: AISummaryRepository,
        outcome_repo: RecommendationOutcomeRepository,
        llm_client: BaseLLMClient,
        task_service: TaskService,
    ):
        self.ai_profile_repo = ai_profile_repo
        self.ai_recommendation_repo = ai_recommendation_repo
        self.ai_summary_repo = ai_summary_repo
        self.outcome_repo = outcome_repo
        self.validator = LLMResponseValidator(llm_client)
        self.task_service = task_service

    async def get_or_create_profile(self, user_id: UUID) -> AIUserProfile:
        profile = await self.ai_profile_repo.get_by_user_id(user_id)
        if not profile:
            profile = AIUserProfile(user_id=str(user_id))
            await self.ai_profile_repo.create(profile)
        return profile

    async def list_pending_recommendations(self, user_id: UUID) -> list[AIRecommendation]:
        return await self.ai_recommendation_repo.list_pending_recommendations(user_id)

    async def update_recommendation_status(
        self, user_id: UUID, recommendation_id: UUID, data: AIRecommendationUpdate
    ) -> AIRecommendation | None:
        rec = await self.ai_recommendation_repo.get_recommendation(
            user_id, recommendation_id
        )
        if not rec:
            return None

        update_args = {"status": data.decision}
        if data.payload is not None:
            update_args["payload"] = data.payload

        return await self.ai_recommendation_repo.update(rec, **update_args)

    async def generate_starter_plan(
        self, 
        user_profile: UserProfile, 
        fixed_blocks: list[FixedBlock], 
        calendar_events: list, 
        day_type: str = "generic",
        extra_prompt: str = ""
    ) -> StarterPlanner:
        from backend.agents.starter_planner_agent import build_starter_planner_graph
        graph = build_starter_planner_graph()
        
        # Invoke the graph with the initial state
        initial_state = {
            "user_profile": user_profile,
            "fixed_blocks": fixed_blocks,
            "calendar_events": calendar_events,
            "day_type": day_type,
            "extra_prompt": extra_prompt,
        }
        
        # LangGraph invoke is synchronous by default unless we use aio methods.
        # ChatOllama supports async, but invoke() blocks. Let's use ainvoke().
        result_state = await graph.ainvoke(initial_state)
        
        if result_state.get("error"):
            raise Exception(f"Failed to generate plan: {result_state['error']}")
            
        return result_state["planner"]

    async def generate_summary(
        self,
        user_id: UUID,
        period_start: str,
        period_end: str,
        period_type: str, # "day" or "week"
        extra_prompt: str = ""
    ) -> PlannerSummaryResponse:
        
        # Parse dates
        try:
            start_dt = datetime.strptime(period_start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_dt = datetime.strptime(period_end, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
        except ValueError:
            start_dt = datetime.now(timezone.utc)
            end_dt = start_dt

        counts = await self.task_service.get_task_status_counts(user_id, start_dt, end_dt)
        
        # basic metrics
        completed_tasks = counts.get("completed", 0)
        missed_tasks = counts.get("pending_not_done", 0) + counts.get("not_done", 0)
        partial_tasks = counts.get("partial_not_done", 0)
        reschedule_count = counts.get("rescheduled", 0)

        strategy = WeeklySummaryPromptStrategy()
        user_prompt = strategy.build_user_prompt(
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            completed_tasks=completed_tasks,
            missed_tasks=missed_tasks,
            partial_tasks=partial_tasks,
            reschedule_count=reschedule_count,
            extra_prompt=extra_prompt
        )

        from backend.schemas.ai_engine_schema import PlannerSummary
        summary: PlannerSummary = await self.validator.generate_and_parse(
            system_prompt=strategy.system_prompt,
            user_prompt=user_prompt,
            model_cls=PlannerSummary
        )

        response = PlannerSummaryResponse.model_validate(summary, from_attributes=True)

        if period_type == "week":
            # Persist to database
            db_summary = AISummary(
                user_id=str(user_id),
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                summary_text=summary.summary_text,
                wins=[w.model_dump() for w in summary.wins],
                issues=[i.model_dump() for i in summary.issues],
                suggestions=[s.model_dump() for s in summary.suggestions],
            )
            created = await self.ai_summary_repo.create(db_summary)
            response.id = created.id
            response.created_at = created.created_at

        return response

    async def apply_recommendation(
        self, user_id: UUID, recommendation: AIRecommendation, user_overrides: dict = None
    ) -> RecommendationOutcome:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Applying recommendation {recommendation.id} for user {user_id}")
        
        payload = recommendation.payload or {}
        if user_overrides:
            payload.update(user_overrides)
            
        kind = recommendation.kind
        
        if kind == "move_activity_time":
            logger.info(f"Executing logic for recommendation kind {kind}")
            # Step 1: LLM decides exact parameters if payload is ambiguous
            from backend.agents.recommendation_agent import RecommendationAgent
            agent = RecommendationAgent()
            prompt = f"Decide execution parameters for moving activity {recommendation.target_activity_id} to new time. Original payload: {json.dumps(payload)}"
            llm_decision_str = await agent._call_llm(prompt)
            
            try:
                decision = json.loads(llm_decision_str)
            except json.JSONDecodeError:
                decision = payload # fallback to programmatic payload
                
            logger.info(f"LLM decision for execution: {decision}")
            
            # Step 2: Programmatically apply to DB via task_service
            # e.g., fetch task and update start_time (Currently a stub)
            applied_change_ref = {"action": "moved_activity", "details": decision}
            
        else:
            logger.warning(f"No execution strategy found for kind: {kind}")
            applied_change_ref = {"error": "Unsupported recommendation kind"}

        # Record outcome
        outcome = RecommendationOutcome(
            recommendation_id=str(recommendation.id),
            user_id=str(user_id),
            decision="accepted",
            applied_change_ref=applied_change_ref
        )
        
        await self.outcome_repo.create(outcome)
        
        recommendation.status = "applied"
        await self.ai_recommendation_repo.update(recommendation, status="applied")
        
        logger.info(f"Successfully recorded outcome for recommendation {recommendation.id}")
        return outcome