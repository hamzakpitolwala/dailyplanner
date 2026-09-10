import asyncio
import os
import urllib.parse
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv('../.env')

async def main():
    """Main."""
    db_url = os.getenv('DATABASE_URL')
    if '?' in db_url:
        db_url = db_url.split('?')[0]
    db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(db_url, connect_args={"ssl": "require"})
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tasks_start_time ON tasks (start_time)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tasks_due_date ON tasks (due_date)"))
            print("Successfully added indexes to tasks table.")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(main())
