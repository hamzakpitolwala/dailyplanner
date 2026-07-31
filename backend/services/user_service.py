from uuid import UUID
from sqlalchemy.orm import Session
import datetime
from backend.db.models.core import UserProfile, Category, Task
from backend.db.models.templates import PlannerTemplate, TemplateTask
from backend.schemas.core_schema import UserProfileUpdate

class UserService:
    def get_user_profile(self, db: Session, user_id: UUID) -> UserProfile:
        profile = db.query(UserProfile).filter(UserProfile.user_id == str(user_id)).first()
        if not profile:
            profile = UserProfile(user_id=str(user_id))
            db.add(profile)
            db.commit()
            db.refresh(profile)
            
        today_str = datetime.date.today().isoformat()
        if profile.last_login_date != today_str:
            profile.last_login_date = today_str
            db.commit()
            
            # Perform daily reset if an active planner is selected
            if profile.active_planner_id:
                self._apply_planner_for_today(db, str(user_id), profile.active_planner_id, today_str)
                
        return profile

    def _apply_planner_for_today(self, db: Session, user_id_str: str, template_id: str, today_str: str):
        # 1. Fetch template tasks
        template_tasks = db.query(TemplateTask).filter(TemplateTask.template_id == template_id).all()
        
        # 2. Auto-mark unfinished tasks from previous days
        past_unfinished = db.query(Task).filter(
            Task.user_id == user_id_str,
            Task.due_date < f"{today_str}T00:00:00",
            Task.status.in_(["pending", "partial", "in_progress"])
        ).all()
        
        for t in past_unfinished:
            if t.status == "pending":
                t.status = "pending_not_done"
            else:
                t.status = "partial_not_done"
        
        db.commit()

        # 3. Delete any existing tasks for today (or pending from yesterday that are now irrelevant? The user requested to reset)
        # Actually, let's just generate new tasks for today. We could preserve yesterday's tasks as completed.
        # But to avoid duplicate generating if we somehow re-run this, we can delete today's tasks first.
        db.query(Task).filter(
            Task.user_id == user_id_str,
            Task.due_date >= f"{today_str}T00:00:00",
            Task.due_date <= f"{today_str}T23:59:59"
        ).delete(synchronize_session=False)
        
        # 3. Create new tasks from template tasks
        for tt in template_tasks:
            # Map category label to category ID if it exists
            cat_id = None
            if tt.category_label:
                cat = db.query(Category).filter(Category.user_id == user_id_str, Category.name == tt.category_label).first()
                if cat:
                    cat_id = cat.id
            
            start_time = None
            due_date = None
            if tt.target_time:
                start_time = datetime.datetime.fromisoformat(f"{today_str}T{tt.target_time}")
                due_date = start_time + datetime.timedelta(minutes=tt.duration_minutes)
            else:
                start_time = datetime.datetime.fromisoformat(f"{today_str}T00:00:00")
                due_date = start_time + datetime.timedelta(minutes=tt.duration_minutes)
                
            new_task = Task(
                user_id=user_id_str,
                category_id=cat_id,
                title=tt.title,
                description=tt.description,
                priority=tt.priority,
                status="pending",
                checklist=tt.checklist,
                source_template_name=None, # Or we could fetch template name
                start_time=start_time,
                due_date=due_date
            )
            db.add(new_task)
            db.commit() # commit individually to prevent uuid errors
        
        # Ensure the deletion is committed even if there were no template tasks
        db.commit()

    def update_user_profile(self, db: Session, user_id: UUID, data: UserProfileUpdate) -> UserProfile:
        profile = self.get_user_profile(db, user_id)
        
        # Check if this is the transition to onboarding_completed
        was_completed = profile.onboarding_completed
        is_completed = data.onboarding_completed if data.onboarding_completed is not None else was_completed
        
        # Check if active planner is changing
        old_planner = profile.active_planner_id
        
        for field, value in data.model_dump(exclude_unset=True).items():
            # SQLAlchemy expects int for boolean columns mapped as Integer
            if isinstance(value, bool):
                value = 1 if value else 0
            setattr(profile, field, value)
            
        db.commit()
        db.refresh(profile)
        
        # If active planner changed, apply it immediately for today
        new_planner = profile.active_planner_id
        if new_planner and new_planner != old_planner:
            today_str = datetime.date.today().isoformat()
            self._apply_planner_for_today(db, str(user_id), new_planner, today_str)

        # If completing onboarding for the first time, generate default categories and templates
        if is_completed and not was_completed:
            self._generate_default_categories(db, user_id)
            self._generate_default_templates(db, user_id, profile)
            
        return profile

    def _generate_default_templates(self, db: Session, user_id: UUID, profile: UserProfile):
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
        db.add(t1)
        db.commit()
        db.refresh(t1)

        db.add(t2)
        db.commit()
        db.refresh(t2)
        
        tt1 = TemplateTask(template_id=t1.id, title="Morning Review", description="Review goals and daily plan.", target_time="09:00:00")
        tt2 = TemplateTask(template_id=t1.id, title="Core Work Session", description="Deep work based on goals.", target_time="10:00:00")
        tt3 = TemplateTask(template_id=t2.id, title="Intensive Block", description="Uninterrupted focus session.", target_time="08:00:00")
        tt4 = TemplateTask(template_id=t2.id, title="Cool-down", description="Wrap up and plan tomorrow.", target_time="17:00:00")
        
        db.add(tt1)
        db.commit()
        db.add(tt2)
        db.commit()
        db.add(tt3)
        db.commit()
        db.add(tt4)
        db.commit()

    def _generate_default_categories(self, db: Session, user_id: UUID):
        defaults = [
            {"name": "Work", "color_hex": "#3538cd"},
            {"name": "Study", "color_hex": "#b54708"},
            {"name": "Fitness", "color_hex": "#276749"},
            {"name": "Personal", "color_hex": "#9c27b0"},
        ]
        for c in defaults:
            # Avoid duplicates
            existing = db.query(Category).filter(
                Category.user_id == str(user_id),
                Category.name == c["name"]
            ).first()
            if not existing:
                cat = Category(user_id=str(user_id), name=c["name"], color_hex=c["color_hex"])
                db.add(cat)
                db.commit() # Commit individually to avoid postgres string UUID insertmanyvalues sentinel bug
