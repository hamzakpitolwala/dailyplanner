import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.db.database import engine
from sqlalchemy import text

async def main():
    """Main."""
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE template_tasks ADD COLUMN requires_reason BOOLEAN DEFAULT FALSE"))
            print("Added requires_reason")
        except Exception as e:
            print("requires_reason error:", e)
            
        try:
            await conn.execute(text("ALTER TABLE template_tasks ADD COLUMN allows_alternate BOOLEAN DEFAULT FALSE"))
            print("Added allows_alternate")
        except Exception as e:
            print("allows_alternate error:", e)

if __name__ == "__main__":
    asyncio.run(main())
