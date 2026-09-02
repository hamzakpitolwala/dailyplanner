from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db

# Repositories
from backend.db.repositories.user import UserRepository, UserProfileRepository
from backend.db.repositories.task import TaskRepository, CategoryRepository
from backend.db.repositories.template import TemplateRepository, TemplateTaskRepository
from backend.db.repositories.integration import IntegrationRepository
from backend.db.repositories.ai_record import (
    AIUserProfileRepository, 
    AIRecommendationRepository, 
    AISummaryRepository,
    RecommendationOutcomeRepository
)
from backend.db.repositories.fixed_block import FixedBlockRepository
from backend.db.repositories.analytics import AnalyticsRepository

# Services
from backend.services.auth_services import AuthService
from backend.services.user_service import UserService
from backend.services.task_service import TaskService
from backend.services.template_service import TemplateService
from backend.services.integration_service import IntegrationService
from backend.services.ai_engine_service import AIEngineService
from backend.services.llm_client import OllamaClient
from backend.services.analytics_service import AnalyticsService
from backend.core.cache import memory_cache

from backend.agents.state_machine import StateMachine
from backend.agents.orchestrator import Orchestrator
from backend.agents.memory_manager import MemoryManager
from backend.services.memory_service import MemoryService
from backend.agents.workers.planner import PlannerChangeWorker
from backend.agents.workers.insight import InsightWorker
from backend.agents.workers.conversation import ConversationWorker
from backend.agents.verification import VerificationLayer
from backend.services.chat_history_service import ChatHistoryService

# --- Repository Factory Functions ---

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_profile_repository(db: AsyncSession = Depends(get_db)) -> UserProfileRepository:
    return UserProfileRepository(db)

def get_task_repository(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)

def get_category_repository(db: AsyncSession = Depends(get_db)) -> CategoryRepository:
    return CategoryRepository(db)

def get_template_repository(db: AsyncSession = Depends(get_db)) -> TemplateRepository:
    return TemplateRepository(db)

def get_template_task_repository(db: AsyncSession = Depends(get_db)) -> TemplateTaskRepository:
    return TemplateTaskRepository(db)

def get_integration_repository(db: AsyncSession = Depends(get_db)) -> IntegrationRepository:
    return IntegrationRepository(db)

def get_ai_user_profile_repository(db: AsyncSession = Depends(get_db)) -> AIUserProfileRepository:
    return AIUserProfileRepository(db)

def get_ai_recommendation_repository(db: AsyncSession = Depends(get_db)) -> AIRecommendationRepository:
    return AIRecommendationRepository(db)

def get_ai_summary_repository(db: AsyncSession = Depends(get_db)) -> AISummaryRepository:
    return AISummaryRepository(db)

def get_recommendation_outcome_repository(db: AsyncSession = Depends(get_db)) -> RecommendationOutcomeRepository:
    return RecommendationOutcomeRepository(db)

def get_fixed_block_repository(db: AsyncSession = Depends(get_db)) -> FixedBlockRepository:
    return FixedBlockRepository(db)

def get_llm_client() -> OllamaClient:
    return OllamaClient(model="qwen2.5:7b")

def get_analytics_repository(db: AsyncSession = Depends(get_db)) -> AnalyticsRepository:
    return AnalyticsRepository(db)

# --- Service Factory Functions ---

def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    return AuthService(user_repo=user_repo)

def get_user_service(
    user_profile_repo: UserProfileRepository = Depends(get_user_profile_repository),
    category_repo: CategoryRepository = Depends(get_category_repository),
    template_repo: TemplateRepository = Depends(get_template_repository),
    template_task_repo: TemplateTaskRepository = Depends(get_template_task_repository),
) -> UserService:
    return UserService(
        user_profile_repo=user_profile_repo,
        category_repo=category_repo,
        template_repo=template_repo,
        template_task_repo=template_task_repo,
    )



def get_integration_service(
    integration_repo: IntegrationRepository = Depends(get_integration_repository)
) -> IntegrationService:
    return IntegrationService(integration_repo=integration_repo)

def get_task_service(
    task_repo: TaskRepository = Depends(get_task_repository),
    category_repo: CategoryRepository = Depends(get_category_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> TaskService:
    return TaskService(
        task_repo=task_repo,
        category_repo=category_repo,
        user_repo=user_repo,
    )

def get_template_service(
    template_repo: TemplateRepository = Depends(get_template_repository),
    template_task_repo: TemplateTaskRepository = Depends(get_template_task_repository),
    task_repo: TaskRepository = Depends(get_task_repository),
) -> TemplateService:
    return TemplateService(
        template_repo=template_repo,
        template_task_repo=template_task_repo,
        task_repo=task_repo,
    )

def get_ai_engine_service(
    ai_profile_repo: AIUserProfileRepository = Depends(get_ai_user_profile_repository),
    ai_recommendation_repo: AIRecommendationRepository = Depends(get_ai_recommendation_repository),
    ai_summary_repo: AISummaryRepository = Depends(get_ai_summary_repository),
    outcome_repo: RecommendationOutcomeRepository = Depends(get_recommendation_outcome_repository),
    llm_client: OllamaClient = Depends(get_llm_client),
    task_service: TaskService = Depends(get_task_service),
) -> AIEngineService:
    return AIEngineService(
        ai_profile_repo=ai_profile_repo,
        ai_recommendation_repo=ai_recommendation_repo,
        ai_summary_repo=ai_summary_repo,
        outcome_repo=outcome_repo,
        llm_client=llm_client,
        task_service=task_service,
    )

def get_analytics_service(
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository)
) -> AnalyticsService:
    return AnalyticsService(analytics_repo=analytics_repo)

from backend.services.calendar_sync_manager import CalendarSyncManager
from backend.agents.recommendation_agent import RecommendationAgent
from backend.agents.chat_agent import PersonalizedChatAgent

def get_calendar_sync_manager(
    integration_service: IntegrationService = Depends(get_integration_service),
    task_service: TaskService = Depends(get_task_service),
) -> CalendarSyncManager:
    return CalendarSyncManager(
        integration_service=integration_service,
        task_service=task_service,
    )

def get_recommendation_agent() -> RecommendationAgent:
    return RecommendationAgent()

def get_chat_agent() -> PersonalizedChatAgent:
    return PersonalizedChatAgent()

# --- Agent Multi-Agent Dependencies ---

def get_state_machine(db: AsyncSession = Depends(get_db)) -> StateMachine:
    return StateMachine(db)

def get_orchestrator(llm_client: OllamaClient = Depends(get_llm_client)) -> Orchestrator:
    return Orchestrator(llm_client)

def get_memory_manager(db: AsyncSession = Depends(get_db)) -> MemoryManager:
    return MemoryManager(db)

def get_memory_service(
    memory_manager: MemoryManager = Depends(get_memory_manager),
    llm_client: OllamaClient = Depends(get_llm_client)
) -> MemoryService:
    return MemoryService(memory_manager, llm_client)

def get_planner_worker(llm_client: OllamaClient = Depends(get_llm_client)) -> PlannerChangeWorker:
    return PlannerChangeWorker(llm_client)

def get_insight_worker(llm_client: OllamaClient = Depends(get_llm_client)) -> InsightWorker:
    return InsightWorker(llm_client)

def get_conversation_worker(llm_client: OllamaClient = Depends(get_llm_client)) -> ConversationWorker:
    return ConversationWorker(llm_client)

def get_verification_layer() -> VerificationLayer:
    return VerificationLayer()

def get_chat_history_service() -> ChatHistoryService:
    return ChatHistoryService()

