from dotenv import load_dotenv
load_dotenv()
from backend.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        # Drop ai_user_profiles if it exists
        conn.execute(text("DROP TABLE IF EXISTS ai_user_profiles CASCADE;"))
        
        # Create user_profiles
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id uuid PRIMARY KEY,
            user_id uuid REFERENCES users(id) ON DELETE CASCADE UNIQUE NOT NULL,
            goals VARCHAR(255),
            focus_times VARCHAR(255),
            typical_disruptions VARCHAR(255),
            structure_preference VARCHAR(255),
            ai_guidance_level VARCHAR(255),
            onboarding_completed INTEGER DEFAULT 0 NOT NULL,
            personality_type VARCHAR(50),
            productivity_velocity FLOAT DEFAULT 1.0 NOT NULL,
            ai_inferred_traits JSON,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
        """))
        conn.commit()
        print("Database migrated successfully.")
    except Exception as e:
        print("Error migrating DB:", e)
