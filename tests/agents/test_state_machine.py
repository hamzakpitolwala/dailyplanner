import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.state_machine import StateMachine, WorkflowState

@pytest.mark.asyncio
async def test_workflow_state_transitions(db_session: AsyncSession):
    machine = StateMachine(db_session)
    user_id = uuid4()
    
    from backend.db.models.core import User
    user = User(id=user_id, email=f"test_{user_id}@test.com", hashed_password="hash")
    db_session.add(user)
    await db_session.commit()
        
    run = await machine.create_workflow(user_id=user_id)
    assert run.state == WorkflowState.RECEIVED.value
    
    run = await machine.transition_state(run.id, WorkflowState.CLASSIFIED, {"intents": [{"type": "planner_change"}]})
    assert run.state == WorkflowState.CLASSIFIED.value
    assert len(run.intents) == 1
    
    run = await machine.transition_state(run.id, WorkflowState.COMPLETED)
    assert run.state == WorkflowState.COMPLETED.value
