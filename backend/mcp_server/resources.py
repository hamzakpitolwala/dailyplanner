import logging
from typing import Optional
from uuid import UUID

from backend.mcp_server import mcp
from backend.db.database import SessionLocal
from backend.db.repositories.user import UserRepository, UserProfileRepository
from backend.db.repositories.fixed_block import FixedBlockRepository

logger = logging.getLogger(__name__)

@mcp.resource("dailyplanner://user/{user_id}/profile")
async def get_user_profile(user_id: str) -> str:
    """Get the user's profile, goals, and preferences."""
    db = SessionLocal()
    try:
        profile_repo = UserProfileRepository(db)
        profile = await profile_repo.get_profile(UUID(user_id))
        
        if not profile:
            return "No profile found."
            
        return f"""
User Profile:
- Name: {profile.username or 'Unknown'}
- Goals: {profile.goals}
- Focus Times: {profile.focus_times}
- Typical Disruptions: {profile.typical_disruptions}
- Structure Preference: {profile.structure_preference}
- AI Guidance Level: {profile.ai_guidance_level}
        """.strip()
    finally:
        await db.close()

@mcp.resource("dailyplanner://user/{user_id}/fixed-blocks")
async def get_user_fixed_blocks(user_id: str) -> str:
    """Get the user's fixed blocks (routines/habits)."""
    db = SessionLocal()
    try:
        fixed_block_repo = FixedBlockRepository(db)
        blocks = await fixed_block_repo.list_fixed_blocks(UUID(user_id))
        
        if not blocks:
            return "No fixed blocks."
            
        text = "Fixed Blocks:\n"
        for b in blocks:
            text += f"- {b.name}: {b.start_time}-{b.end_time} on days {b.days_of_week}\n"
        return text.strip()
    finally:
        await db.close()
