import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from backend.db.models.agent import Memory

logger = logging.getLogger(__name__)

class MemoryManager:
    """Memorymanager."""
    def __init__(self, db: AsyncSession):
        """  init  ."""
        self.db = db

    async def get_memories(
        self, 
        user_id: UUID, 
        scope: Optional[str] = None, 
        session_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[Memory]:
        """Fetch active memories for a user, optionally filtered by scope or session."""
        query = select(Memory).where(
            and_(
                Memory.user_id == user_id,
                Memory.is_active == 1
            )
        )
        
        if scope:
            query = query.where(Memory.scope == scope)
            
        if session_id:
            query = query.where(Memory.session_id == session_id)
            
        query = query.order_by(desc(Memory.importance), desc(Memory.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_memory(
        self, 
        user_id: UUID, 
        scope: str, 
        content: str, 
        structured_value: Optional[Dict[str, Any]] = None,
        session_id: Optional[UUID] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        confidence: float = 1.0,
        importance: float = 1.0
    ) -> Memory:
        """Add a new memory for the user."""
        memory = Memory(
            user_id=user_id,
            scope=scope,
            content=content,
            structured_value=structured_value,
            session_id=session_id,
            category=category,
            source=source,
            confidence=confidence,
            importance=importance
        )
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def format_memories_for_prompt(self, user_id: UUID, session_id: Optional[UUID] = None) -> str:
        """Format the user's memories into a readable string for the LLM prompt context."""
        # Fetch high-level profile/behavioral memories
        core_memories = await self.get_memories(user_id, scope="user_profile", limit=10)
        behavioral_memories = await self.get_memories(user_id, scope="behavioral", limit=10)
        
        # Fetch recent session/episodic memories if session_id is provided
        session_memories = []
        if session_id:
            session_memories = await self.get_memories(user_id, session_id=session_id, limit=5)
            
        lines = []
        if core_memories:
            lines.append("User Preferences & Goals:")
            for m in core_memories:
                lines.append(f"- {m.content}")
                
        if behavioral_memories:
            lines.append("\nObserved Patterns:")
            for m in behavioral_memories:
                lines.append(f"- {m.content}")
                
        if session_memories:
            lines.append("\nRecent Conversation Context:")
            for m in session_memories:
                lines.append(f"- {m.content}")
                
        return "\n".join(lines) if lines else "No prior memories found."
