from typing import TypedDict, List, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from backend.schemas.ai_engine_schema import StarterPlanner
from backend.db.models.core import UserProfile, FixedBlock

class PlannerState(TypedDict):
    user_profile: UserProfile
    fixed_blocks: List[FixedBlock]
    calendar_events: List[Any]
    day_type: str
    extra_prompt: str
    planner: Optional[StarterPlanner]
    error: Optional[str]

async def generate_plan(state: PlannerState) -> dict:
    llm = ChatOllama(model="llama3.1", temperature=0)
    structured_llm = llm.with_structured_output(StarterPlanner)

    system_prompt = """You are an assistant that designs a structured daily planner template."""
    
    profile = state["user_profile"]
    fixed_blocks = state["fixed_blocks"]
    calendar_events = state["calendar_events"]
    extra_prompt = state["extra_prompt"]
    day_type = state["day_type"]

    blocks_text = "\n".join([f"- {b.name}: {b.start_time}-{b.end_time} on days {b.days_of_week}" for b in fixed_blocks])
    events_text = "\n".join([f"- {e.summary}: {e.start_time} to {e.end_time}" for e in calendar_events]) if calendar_events else "None"
    
    user_prompt = f"""
User profile:
- Goals: {profile.goals}
- Focus times: {profile.focus_times}
- Disruptions: {profile.typical_disruptions}
- Structure preference: {profile.structure_preference}
- AI guidance preference: {profile.ai_guidance_level}

Fixed blocks:
{blocks_text or "None"}

Today's calendar events:
{events_text}

Request: Create a starter plan for a {day_type} day.
{("Additional User Instruction: " + extra_prompt) if extra_prompt else ""}

Constraints:
- Respect fixed blocks (do not schedule conflicting tasks).
- Create a realistic day with breaks.
- Focus more time on the main goal.
"""
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        result = await structured_llm.ainvoke(messages)
        return {"planner": result, "error": None}
    except Exception as e:
        return {"planner": None, "error": str(e)}

def build_starter_planner_graph():
    workflow = StateGraph(PlannerState)
    workflow.add_node("generate_plan", generate_plan)
    workflow.add_edge(START, "generate_plan")
    workflow.add_edge("generate_plan", END)
    
    return workflow.compile()
