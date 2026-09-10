from enum import Enum
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models.agent import WorkflowRun
from sqlalchemy import select
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

class WorkflowState(str, Enum):
    """Workflowstate."""
    RECEIVED = "RECEIVED"
    CLASSIFIED = "CLASSIFIED"
    CONTEXT_RETRIEVED = "CONTEXT_RETRIEVED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    PLAN_CREATED = "PLAN_CREATED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class StateMachine:
    """Statemachine."""
    def __init__(self, db: AsyncSession):
        """  init  ."""
        self.db = db

    async def create_workflow(self, user_id: UUID, conversation_id: Optional[UUID] = None) -> WorkflowRun:
        """Create workflow."""
        run = WorkflowRun(
            user_id=user_id,
            conversation_id=conversation_id,
            state=WorkflowState.RECEIVED.value
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def get_workflow(self, run_id: UUID) -> Optional[WorkflowRun]:
        """Get workflow."""
        result = await self.db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))
        return result.scalar_one_or_none()

    async def transition_state(self, run_id: UUID, new_state: WorkflowState, updates: Dict[str, Any] = None) -> WorkflowRun:
        """Transition state."""
        run = await self.get_workflow(run_id)
        if not run:
            raise ValueError(f"WorkflowRun {run_id} not found")
            
        run.state = new_state.value
        if updates:
            for k, v in updates.items():
                if hasattr(run, k):
                    setattr(run, k, v)
                    
        await self.db.commit()
        await self.db.refresh(run)
        return run
