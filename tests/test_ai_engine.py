"""Unit and integration tests for the AI Engine service and models.

Covers:
- Profile creation and retrieval via AIEngineService
- Recommendation filtering by status and user ownership
- Recommendation status updates (accepted, dismissed)
- Non-existent / unowned recommendation update handling
"""

import uuid
import pytest
from sqlalchemy.orm import Session

from backend.core.security import hash_password
from backend.db.models.ai_engine import AIUserProfile, AIRecommendation
from backend.db.models.core import User
from backend.schemas.ai_engine_schema import (
    AIUserProfileResponse,
    AIRecommendationUpdate,
    AIRecommendationResponse,
)
from backend.services.ai_engine_service import AIEngineService

service = AIEngineService()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Helper fixture to create a registered user in the test database."""
    unique_email = f"ai_user_{uuid.uuid4().hex[:8]}@example.com"
    user = User(email=unique_email, hashed_password=hash_password("secret1234"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session: Session) -> User:
    """Helper fixture to create a second registered user in the test database."""
    unique_email = f"ai_user2_{uuid.uuid4().hex[:8]}@example.com"
    user = User(email=unique_email, hashed_password=hash_password("secret1234"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestAIEngineServiceProfile:
    def test_get_or_create_profile_creates_new(self, db_session: Session, test_user: User):
        profile = service.get_or_create_profile(db_session, uuid.UUID(test_user.id))
        assert profile is not None
        assert profile.user_id == test_user.id
        assert profile.productivity_velocity == 1.0

        # Validate with Pydantic response schema
        validated = AIUserProfileResponse.model_validate(profile)
        assert str(validated.user_id) == test_user.id

    def test_get_or_create_profile_returns_existing(self, db_session: Session, test_user: User):
        profile1 = service.get_or_create_profile(db_session, uuid.UUID(test_user.id))
        profile1.personality_type = "Achiever"
        db_session.commit()

        profile2 = service.get_or_create_profile(db_session, uuid.UUID(test_user.id))
        assert profile2.id == profile1.id
        assert profile2.personality_type == "Achiever"


class TestAIEngineServiceRecommendations:
    def test_list_pending_recommendations(self, db_session: Session, test_user: User, other_user: User):
        rec1 = AIRecommendation(
            user_id=test_user.id,
            recommendation_text="Take a 10-minute break",
            rationale="High cognitive load detected",
            suggested_changes={"break_minutes": 10},
            status="pending",
        )
        rec2 = AIRecommendation(
            user_id=test_user.id,
            recommendation_text="Reschedule evening task",
            suggested_changes={"move_to": "tomorrow"},
            status="accepted",
        )
        rec_other = AIRecommendation(
            user_id=other_user.id,
            recommendation_text="Other user recommendation",
            suggested_changes={},
            status="pending",
        )
        db_session.add_all([rec1, rec2, rec_other])
        db_session.commit()

        pending = service.list_pending_recommendations(db_session, uuid.UUID(test_user.id))
        assert len(pending) == 1
        assert pending[0].id == rec1.id
        assert pending[0].recommendation_text == "Take a 10-minute break"

        # Validate schema mapping
        validated = AIRecommendationResponse.model_validate(pending[0])
        assert str(validated.id) == rec1.id
        assert validated.status == "pending"

    def test_update_recommendation_status(self, db_session: Session, test_user: User):
        rec = AIRecommendation(
            user_id=test_user.id,
            recommendation_text="Focus on high priority task",
            suggested_changes={},
            status="pending",
        )
        db_session.add(rec)
        db_session.commit()
        db_session.refresh(rec)

        update_payload = AIRecommendationUpdate(status="accepted")
        updated = service.update_recommendation_status(
            db_session, uuid.UUID(test_user.id), uuid.UUID(rec.id), update_payload
        )
        assert updated is not None
        assert updated.status == "accepted"

    def test_update_recommendation_status_unowned_or_missing(
        self, db_session: Session, test_user: User, other_user: User
    ):
        rec_other = AIRecommendation(
            user_id=other_user.id,
            recommendation_text="Private rec",
            suggested_changes={},
            status="pending",
        )
        db_session.add(rec_other)
        db_session.commit()

        update_payload = AIRecommendationUpdate(status="dismissed")
        # Attempt to update someone else's recommendation
        res = service.update_recommendation_status(
            db_session, uuid.UUID(test_user.id), uuid.UUID(rec_other.id), update_payload
        )
        assert res is None

        # Attempt to update non-existent recommendation ID
        res_fake = service.update_recommendation_status(
            db_session, uuid.UUID(test_user.id), uuid.uuid4(), update_payload
        )
        assert res_fake is None
