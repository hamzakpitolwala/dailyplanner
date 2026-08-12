import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sqlalchemy import text
from backend.db.database import engine

async def migrate():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE template_tasks ALTER COLUMN target_time TYPE VARCHAR(8) USING target_time::VARCHAR(8);"))
            print("Altered target_time to VARCHAR(8)")
        except Exception as e:
            print("Could not alter column:", e)

if __name__ == "__main__":
    asyncio.run(migrate())
