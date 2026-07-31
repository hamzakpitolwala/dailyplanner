from backend.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        with conn.begin():
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN active_planner_id UUID REFERENCES planner_templates(id) ON DELETE SET NULL"))
    except Exception as e:
        print("Error active_planner_id:", e)
        
    try:
        with conn.begin():
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN last_login_date VARCHAR(10)"))
    except Exception as e:
        print("Error last_login_date:", e)

print("Migration completed.")
