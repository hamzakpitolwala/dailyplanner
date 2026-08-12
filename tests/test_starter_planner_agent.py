import pytest
from unittest.mock import AsyncMock, patch

from backend.agents.starter_planner_agent import generate_plan, PlannerState
from backend.db.models.core import UserProfile, FixedBlock
from backend.schemas.ai_engine_schema import StarterPlanner, StarterActivity

@pytest.mark.asyncio
async def test_generate_plan_success():
    # Create mock inputs
    profile = UserProfile(
        goals="Test Goals",
        focus_times="Morning",
        typical_disruptions="None",
        structure_preference="High",
        ai_guidance_level="Proactive"
    )
    
    fixed_blocks = [
        FixedBlock(name="Lunch", start_time="12:00", end_time="13:00", days_of_week=[1,2,3,4,5])
    ]
    
    state = PlannerState(
        user_profile=profile,
        fixed_blocks=fixed_blocks,
        calendar_events=[],
        day_type="work",
        extra_prompt="",
        planner=None,
        error=None
    )
    
    # Mock the LLM's ainvoke method
    mock_llm_chain = AsyncMock()
    mock_planner = StarterPlanner(
        template_name="Test Plan",
        description="Test desc",
        timezone="UTC",
        day_type="generic",
        activities=[
            StarterActivity(title="Morning work", start_time="09:00", end_time="11:00", priority="high")
        ]
    )
    mock_llm_chain.ainvoke.return_value = mock_planner

    # We need to patch ChatOllama.with_structured_output which returns the mock chain
    with patch("backend.agents.starter_planner_agent.ChatOllama") as mock_chat_ollama_cls:
        mock_instance = mock_chat_ollama_cls.return_value
        mock_instance.with_structured_output.return_value = mock_llm_chain
        
        result = await generate_plan(state)
        
        assert result["error"] is None
        assert result["planner"] is not None
        assert result["planner"].template_name == "Test Plan"

@pytest.mark.asyncio
async def test_generate_plan_error():
    profile = UserProfile(
        goals="Test",
        focus_times="Morning",
        typical_disruptions="None",
        structure_preference="High",
        ai_guidance_level="Proactive"
    )
    
    state = PlannerState(
        user_profile=profile,
        fixed_blocks=[],
        calendar_events=[],
        day_type="work",
        extra_prompt="",
        planner=None,
        error=None
    )
    
    mock_llm_chain = AsyncMock()
    mock_llm_chain.ainvoke.side_effect = Exception("LLM Error")

    with patch("backend.agents.starter_planner_agent.ChatOllama") as mock_chat_ollama_cls:
        mock_instance = mock_chat_ollama_cls.return_value
        mock_instance.with_structured_output.return_value = mock_llm_chain
        
        result = await generate_plan(state)
        
        assert result["planner"] is None
        assert result["error"] == "LLM Error"
