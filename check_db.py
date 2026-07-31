from dotenv import load_dotenv
load_dotenv()
from backend.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tasks';"))
    for row in res:
        print(f"tasks.{row[0]}: {row[1]}")
