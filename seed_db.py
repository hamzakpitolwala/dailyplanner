from dotenv import load_dotenv
load_dotenv()
from backend.db.database import SessionLocal, engine, Base
from backend.db.models.core import MissedReason, AlternateActivity

# Force table creation
Base.metadata.create_all(bind=engine)

db = SessionLocal()

reasons = [
    "I was too busy",
    "I forgot",
    "I felt tired/sick",
    "An emergency came up",
    "I didn't feel like it"
]

for r in reasons:
    if not db.query(MissedReason).filter(MissedReason.name == r, MissedReason.user_id == None).first():
        db.add(MissedReason(name=r))

alts = [
    "Doing some important work",
    "Resting/Recovering",
    "Spending time with family/friends",
    "Dealing with an emergency"
]

for a in alts:
    if not db.query(AlternateActivity).filter(AlternateActivity.name == a, AlternateActivity.user_id == None).first():
        db.add(AlternateActivity(name=a))

db.commit()
print("Seeding complete")
