from dotenv import load_dotenv
load_dotenv()
from backend.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        # Create missed_reasons
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS missed_reasons (
            id uuid PRIMARY KEY,
            user_id uuid REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL
        );
        """))
        
        # Create alternate_activities
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS alternate_activities (
            id uuid PRIMARY KEY,
            user_id uuid REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL
        );
        """))
        
        # Create task_checkins
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS task_checkins (
            id uuid PRIMARY KEY,
            task_id uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            status VARCHAR(20) NOT NULL,
            missed_reason_id uuid REFERENCES missed_reasons(id) ON DELETE SET NULL,
            alternate_activity_id uuid REFERENCES alternate_activities(id) ON DELETE SET NULL,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
        """))
        conn.commit()
        print("Tables created")
    except Exception as e:
        print("Error:", e)
