from uuid import UUID
from sqlalchemy.orm import Session

from backend.db.models.ai_engine import AIRecommendation, AIUserProfile
from backend.schemas.ai_engine_schema import AIRecommendationUpdate


class AIEngineService:
    """Service layer for managing AI user profiles and generated recommendations."""

    def get_or_create_profile(self, db: Session, user_id: UUID) -> AIUserProfile:
        profile = (
            db.query(AIUserProfile).filter(AIUserProfile.user_id == user_id).first()
        )
        if not profile:
            profile = AIUserProfile(user_id=user_id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    def list_pending_recommendations(self, db: Session, user_id: UUID) -> list[AIRecommendation]:
        return (
            db.query(AIRecommendation)
            .filter(AIRecommendation.user_id == user_id, AIRecommendation.status == "pending")
            .all()
        )

    def update_recommendation_status(
        self, db: Session, user_id: UUID, recommendation_id: UUID, data: AIRecommendationUpdate
    ) -> AIRecommendation | None:
        rec = (
            db.query(AIRecommendation)
            .filter(AIRecommendation.id == recommendation_id, AIRecommendation.user_id == user_id)
            .first()
        )
        if not rec:
            return None

        rec.status = data.status #type: ignore
        db.commit()
        db.refresh(rec)
        return rec