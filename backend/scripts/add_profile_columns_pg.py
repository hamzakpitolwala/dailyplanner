import asyncio
import os
import sys

# Add project root to sys.path so we can import backend module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from backend.db.database import engine

async def migrate():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE user_profiles ADD COLUMN username VARCHAR(255);"))
            print("Added username column.")
        except Exception as e:
            print("Username column might already exist:", e)

        try:
            await conn.execute(text("ALTER TABLE user_profiles ADD COLUMN dob VARCHAR(50);"))
            print("Added dob column.")
        except Exception as e:
            print("DOB column might already exist:", e)

        try:
            await conn.execute(text("ALTER TABLE user_profiles ADD COLUMN gender VARCHAR(50);"))
            print("Added gender column.")
        except Exception as e:
            print("Gender column might already exist:", e)

        try:
            await conn.execute(text("CREATE UNIQUE INDEX ix_user_profiles_username ON user_profiles(username) WHERE username IS NOT NULL;"))
            print("Added unique index for username.")
        except Exception as e:
            print("Index might already exist:", e)

if __name__ == "__main__":
    asyncio.run(migrate())
