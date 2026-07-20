from backend.core.database import SessionLocal, engine
from sqlalchemy import text

def add_columns():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE daily_planners ADD COLUMN template_id INTEGER REFERENCES planner_templates(id);"))
            print("Added template_id to daily_planners")
        except Exception as e:
            print(f"Skipping template_id: {e}")
            
        try:
            conn.execute(text("ALTER TABLE activities ADD COLUMN carried_over_from_id INTEGER REFERENCES activities(id);"))
            print("Added carried_over_from_id to activities")
        except Exception as e:
            print(f"Skipping carried_over_from_id: {e}")
            
        conn.commit()

add_columns()
