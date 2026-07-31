import os
import sqlalchemy as sa
from backend.core.config import settings

engine = sa.create_engine(settings.DATABASE_URL)
with engine.begin() as conn:
    try:
        conn.execute(sa.text("ALTER TABLE tasks ADD COLUMN start_time TIMESTAMP WITH TIME ZONE;"))
        print("Added start_time to tasks.")
    except Exception as e:
        print("Failed to add start_time (maybe it already exists?):", e)
    
    try:
        conn.execute(sa.text("ALTER TABLE template_tasks ADD COLUMN duration_minutes INTEGER DEFAULT 60 NOT NULL;"))
        print("Added duration_minutes to template_tasks.")
    except Exception as e:
        print("Failed to add duration_minutes (maybe it already exists?):", e)
