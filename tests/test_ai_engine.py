import uuid
import pytest
import pytest_asyncio
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


@pytest.fixture
def service(ai_engine_service: AIEngineService) -> AIEngineService:
    return ai_engine_service


@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_user(db_session: Session) -> User:
    """Helper fixture to create a registered user in the test database."""
    unique_email = f"ai_user_{uuid.uuid4().hex[:8]}@example.com"
    user = User(email=unique_email, hashed_password=hash_password("secret1234"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_user(db_session: Session) -> User:
    """Helper fixture to create a second registered user in the test database."""
    unique_email = f"ai_user2_{uuid.uuid4().hex[:8]}@example.com"
    user = User(email=unique_email, hashed_password=hash_password("secret1234"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestAIEngineServiceProfile:
    @pytest.mark.asyncio
    async def test_get_or_create_profile_creates_new(self, service: AIEngineService, test_user: User):
        profile = await service.get_or_create_profile(uuid.UUID(test_user.id))
        assert profile is not None
        assert profile.user_id == test_user.id
        assert profile.productivity_velocity == 1.0

        # Validate with Pydantic response schema
        validated = AIUserProfileResponse.model_validate(profile)
        assert str(validated.user_id) == test_user.id

    @pytest.mark.asyncio
    async def test_get_or_create_profile_returns_existing(self, db_session: Session, service: AIEngineService, test_user: User):
        profile1 = await service.get_or_create_profile(uuid.UUID(test_user.id))
        profile1.personality_type = "Achiever"
        await db_session.commit()

        profile2 = await service.get_or_create_profile(uuid.UUID(test_user.id))
        assert profile2.id == profile1.id
        assert profile2.personality_type == "Achiever"


class TestAIEngineServiceRecommendations:
    @pytest.mark.asyncio
    async def test_list_pending_recommendations(self, db_session: Session, service: AIEngineService, test_user: User, other_user: User):
        rec1 = AIRecommendation(
            user_id=test_user.id,
            title="Take a 10-minute break",
            explanation="High cognitive load detected",
            kind="break_suggestion",
            scope="daily",
            payload={"break_minutes": 10},
            status="pending",
        )
        rec2 = AIRecommendation(
            user_id=test_user.id,
            title="Reschedule evening task",
            explanation="Reschedule evening task",
            kind="task_reschedule",
            scope="daily",
            payload={"move_to": "tomorrow"},
            status="accepted",
        )
        rec_other = AIRecommendation(
            user_id=other_user.id,
            title="Other user recommendation",
            explanation="Other user recommendation",
            kind="generic",
            scope="daily",
            payload={},
            status="pending",
        )
        db_session.add_all([rec1, rec2, rec_other])
        await db_session.commit()

        pending = await service.list_pending_recommendations(uuid.UUID(test_user.id))
        assert len(pending) == 1
        assert pending[0].id == rec1.id
        assert pending[0].title == "Take a 10-minute break"

        # Validate schema mapping
        validated = AIRecommendationResponse.model_validate(pending[0])
        assert str(validated.id) == rec1.id
        assert validated.status == "pending"

    @pytest.mark.asyncio
    async def test_update_recommendation_status(self, db_session: Session, service: AIEngineService, test_user: User):
        rec = AIRecommendation(
            user_id=test_user.id,
            title="Focus on high priority task",
            explanation="Focus on high priority task",
            kind="task_focus",
            scope="daily",
            payload={},
            status="pending",
        )
        db_session.add(rec)
        await db_session.commit()
        await db_session.refresh(rec)

        update_payload = AIRecommendationUpdate(decision="accepted")
        updated = await service.update_recommendation_status(
            uuid.UUID(test_user.id), uuid.UUID(rec.id), update_payload
        )
        assert updated is not None
        assert updated.status == "accepted"

    @pytest.mark.asyncio
    async def test_update_recommendation_status_unowned_or_missing(
        self, db_session: Session, service: AIEngineService, test_user: User, other_user: User
    ):
        rec_other = AIRecommendation(
            user_id=other_user.id,
            title="Private rec",
            explanation="Private rec",
            kind="generic",
            scope="daily",
            payload={},
            status="pending",
        )
        db_session.add(rec_other)
        await db_session.commit()

        update_payload = AIRecommendationUpdate(decision="rejected")
        # Attempt to update someone else's recommendation
        res = await service.update_recommendation_status(
            uuid.UUID(test_user.id), uuid.UUID(rec_other.id), update_payload
        )
        assert res is None

        # Attempt to update non-existent recommendation ID
        res_fake = await service.update_recommendation_status(
            uuid.UUID(test_user.id), uuid.uuid4(), update_payload
        )
        assert res_fake is None
