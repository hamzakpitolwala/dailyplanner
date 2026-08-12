from uuid import UUID
from sqlalchemy import select
from backend.db.models.ai_engine import AIUserProfile, AIRecommendation, AISummary
from backend.db.repositories.base import BaseRepository



class AIUserProfileRepository(BaseRepository[AIUserProfile]):
    """Repository handling AIUserProfile operations."""

    def __init__(self, db):
        super().__init__(AIUserProfile, db)

    async def get_by_user_id(self, user_id: UUID) -> AIUserProfile | None:
        result = await self.db.execute(
            select(AIUserProfile).filter(AIUserProfile.user_id == str(user_id))
        )
        return result.scalars().first()


class AIRecommendationRepository(BaseRepository[AIRecommendation]):
    """Repository handling AIRecommendation operations."""

    def __init__(self, db):
        super().__init__(AIRecommendation, db)

    async def list_pending_recommendations(self, user_id: UUID) -> list[AIRecommendation]:
        result = await self.db.execute(
            select(AIRecommendation).filter(
                AIRecommendation.user_id == str(user_id),
                AIRecommendation.status == "pending",
            )
        )
        return list(result.scalars().all())

    async def get_recommendation(self, user_id: UUID, rec_id: UUID) -> AIRecommendation | None:
        result = await self.db.execute(
            select(AIRecommendation).filter(
                AIRecommendation.id == str(rec_id),
                AIRecommendation.user_id == str(user_id),
            )
        )
        return result.scalars().first()

class AISummaryRepository(BaseRepository[AISummary]):
    """Repository handling AISummary operations."""

    def __init__(self, db):
        super().__init__(AISummary, db)

class RecommendationOutcomeRepository(BaseRepository):
    """Repository handling RecommendationOutcome operations."""

    def __init__(self, db):
        from backend.db.models.ai_engine import RecommendationOutcome
        super().__init__(RecommendationOutcome, db)
