import datetime
from uuid import UUID

from backend.db.models.core import UserProfile, Category
from backend.db.models.templates import PlannerTemplate, TemplateTask
from backend.schemas.core_schema import UserProfileUpdate
from backend.db.repositories.user import UserProfileRepository
from backend.db.repositories.task import CategoryRepository
from backend.db.repositories.template import TemplateRepository, TemplateTaskRepository


class UserService:
    """Service layer managing UserProfiles and initial defaults generation."""

    def __init__(
        self,
        user_profile_repo: UserProfileRepository,
        category_repo: CategoryRepository,
        template_repo: TemplateRepository,
        template_task_repo: TemplateTaskRepository,
    ):
        """  init  ."""
        self.user_profile_repo = user_profile_repo
        self.category_repo = category_repo
        self.template_repo = template_repo
        self.template_task_repo = template_task_repo

    async def get_user_profile(self, user_id: UUID) -> UserProfile:
        """Get user profile."""
        profile = await self.user_profile_repo.get_by_user_id(user_id)
        if not profile:
            profile = UserProfile(user_id=str(user_id))
            await self.user_profile_repo.create(profile)
            
        today_str = datetime.date.today().isoformat()
        if profile.last_login_date != today_str:
            profile = await self.user_profile_repo.update(profile, last_login_date=today_str)
                
        return profile

    async def update_user_profile(
        self, user_id: UUID, data: UserProfileUpdate
    ) -> UserProfile:
        """Update user profile."""
        profile = await self.get_user_profile(user_id)
        
        was_completed = profile.onboarding_completed
        is_completed = (
            data.onboarding_completed
            if data.onboarding_completed is not None
            else was_completed
        )
        
        update_data = {}
        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "username":
                if value == "":
                    value = None
                if value is not None:
                    # Check uniqueness
                    existing = await self.user_profile_repo.get_by_username(value)
                    if existing and existing.id != profile.id:
                        raise ValueError("Username is already taken.")
            
            if isinstance(value, bool):
                value = 1 if value else 0
            update_data[field] = value
            
        await self.user_profile_repo.update(profile, **update_data)

        if is_completed and not was_completed:
            await self._generate_default_categories(user_id)
            await self._generate_default_templates(user_id, profile)
            
        return profile

    async def _generate_default_templates(
        self, user_id: UUID, profile: UserProfile
    ) -> None:
        """ generate default templates."""
        t1 = PlannerTemplate(
            user_id=str(user_id), 
            name="AI Balanced Routine", 
            description=f"Balanced routine focusing on: {profile.goals or 'general goals'}."
        )
        t2 = PlannerTemplate(
            user_id=str(user_id), 
            name="AI Intensive Focus", 
            description=f"Intensive structure tailored for {profile.focus_times or 'deep focus'}."
        )
        await self.template_repo.create(t1)
        await self.template_repo.create(t2)
        
        tt1 = TemplateTask(
            template_id=t1.id,
            title="Morning Review",
            description="Review goals and daily plan.",
            target_time="09:00:00",
        )
        tt2 = TemplateTask(
            template_id=t1.id,
            title="Core Work Session",
            description="Deep work based on goals.",
            target_time="10:00:00",
        )
        tt3 = TemplateTask(
            template_id=t2.id,
            title="Intensive Block",
            description="Uninterrupted focus session.",
            target_time="08:00:00",
        )
        tt4 = TemplateTask(
            template_id=t2.id,
            title="Cool-down",
            description="Wrap up and plan tomorrow.",
            target_time="17:00:00",
        )
        
        await self.template_task_repo.create(tt1)
        await self.template_task_repo.create(tt2)
        await self.template_task_repo.create(tt3)
        await self.template_task_repo.create(tt4)

    async def _generate_default_categories(self, user_id: UUID) -> None:
        """ generate default categories."""
        defaults = [
            {"name": "Work", "color_hex": "#3538cd"},
            {"name": "Study", "color_hex": "#b54708"},
            {"name": "Fitness", "color_hex": "#276749"},
            {"name": "Personal", "color_hex": "#9c27b0"},
        ]
        for c in defaults:
            existing = await self.category_repo.get_by_name(user_id, c["name"])
            if not existing:
                cat = Category(
                    user_id=str(user_id), name=c["name"], color_hex=c["color_hex"]
                )
                await self.category_repo.create(cat)
