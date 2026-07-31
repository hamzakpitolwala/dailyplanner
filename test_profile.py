from backend.db.database import SessionLocal
from backend.services.user_service import UserService
from backend.schemas.core_schema import UserProfileUpdate
from backend.db.models.core import User

db = SessionLocal()
user = db.query(User).first()
service = UserService()
update_data = UserProfileUpdate(goals="Study", onboarding_completed=True)
try:
    service.update_user_profile(db, user.id, update_data)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()

