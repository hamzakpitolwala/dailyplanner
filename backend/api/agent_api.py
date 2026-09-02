import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.api import deps
from backend.core.oauth2 import get_current_user
from backend.schemas.agent_schema import (
    AgentChatRequest, AgentChatResponse, AgentApprovalRequest, 
    ConversationSessionOut, ConversationMessageOut
)
from backend.db.models.agent import WorkflowRun, ConversationSession, ConversationMessage
from backend.agents.state_machine import WorkflowState
from backend.db.models.core import User
from backend.db.models.ai_engine import AIRecommendation, RecommendationOutcome
from backend.services.chat_history_service import ChatHistoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/agent", tags=["agent"])

@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    state_machine: deps.StateMachine = Depends(deps.get_state_machine),
    orchestrator: deps.Orchestrator = Depends(deps.get_orchestrator),
    memory_manager: deps.MemoryManager = Depends(deps.get_memory_manager),
    memory_service: deps.MemoryService = Depends(deps.get_memory_service),
    planner_worker: deps.PlannerChangeWorker = Depends(deps.get_planner_worker),
    insight_worker: deps.InsightWorker = Depends(deps.get_insight_worker),
    conversation_worker: deps.ConversationWorker = Depends(deps.get_conversation_worker),
    verification_layer: deps.VerificationLayer = Depends(deps.get_verification_layer),
    chat_history: ChatHistoryService = Depends(deps.get_chat_history_service),
    template_service: deps.TemplateService = Depends(deps.get_template_service),
):
    """
    Main entry point for multi-agent chat.
    Implements the state machine workflow for intent classification, 
    tool execution, and confirmation handling.
    Messages are persisted to both PostgreSQL and Pinecone.
    """
    
    # 1. Setup Session
    if request.conversation_id:
        session = await db.get(ConversationSession, request.conversation_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        session = ConversationSession(user_id=current_user.id)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
    # Save User Message to PostgreSQL
    user_msg = ConversationMessage(
        conversation_id=session.id,
        user_id=current_user.id,
        role="user",
        content={"text": request.message}
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)
    
    # Store user message in Pinecone (background)
    background_tasks.add_task(
        chat_history.store_message,
        message_id=str(user_msg.id),
        user_id=str(current_user.id),
        conversation_id=str(session.id),
        role="user",
        text=request.message,
    )
    
    # 2. State: RECEIVED
    workflow = await state_machine.create_workflow(user_id=current_user.id, conversation_id=session.id)
    
    # 3. State: CLASSIFIED
    classification = await orchestrator.classify_intent(request.message)
    workflow = await state_machine.transition_state(
        workflow.id, 
        WorkflowState.CLASSIFIED, 
        {"intents": [i.model_dump() for i in classification.intents], "classification": classification.model_dump()}
    )
    
    # 4. Context Retrieval
    memories_text = await memory_manager.format_memories_for_prompt(current_user.id, session.id)
    context = {"memories": memories_text}
    
    # Check if needs clarification
    primary_intent = classification.intents[0] if classification.intents else None
    
    if primary_intent and primary_intent.type == "planner_change":
        templates = await template_service.list_templates(current_user.id)
        context["available_templates"] = [{"id": str(t.id), "name": t.name} for t in templates]
        
    workflow = await state_machine.transition_state(workflow.id, WorkflowState.CONTEXT_RETRIEVED)
    
    if not primary_intent or primary_intent.requires_clarification:
        workflow = await state_machine.transition_state(workflow.id, WorkflowState.NEEDS_CLARIFICATION)
        
        # Route to conversation worker for clarification response
        result = await conversation_worker.process(current_user.id, request.message, context, primary_intent.model_dump() if primary_intent else {})
        
        response_text = result.get("explanation", "Could you clarify what you mean?")
        
        # Save assistant message to PostgreSQL
        ast_msg = ConversationMessage(
            conversation_id=session.id,
            user_id=current_user.id,
            workflow_run_id=workflow.id,
            role="assistant",
            content={"text": response_text}
        )
        db.add(ast_msg)
        await db.commit()
        await db.refresh(ast_msg)
        
        # Store assistant message in Pinecone (background)
        background_tasks.add_task(
            chat_history.store_message,
            message_id=str(ast_msg.id),
            user_id=str(current_user.id),
            conversation_id=str(session.id),
            role="assistant",
            text=response_text,
        )
        
        workflow = await state_machine.transition_state(workflow.id, WorkflowState.WAITING_FOR_USER)
        return AgentChatResponse(
            workflow_id=workflow.id,
            conversation_id=session.id,
            status="waiting_for_user",
            message=response_text
        )
        
    # 5. Route to Specialist Worker
    intent_type = primary_intent.type
    worker_result = {}
    
    if intent_type == "planner_change":
        worker_result = await planner_worker.process(current_user.id, request.message, context, primary_intent.model_dump())
    elif intent_type == "insight":
        worker_result = await insight_worker.process(current_user.id, request.message, context, primary_intent.model_dump())
    else:
        worker_result = await conversation_worker.process(current_user.id, request.message, context, primary_intent.model_dump())
        
    if "error" in worker_result:
        workflow = await state_machine.transition_state(workflow.id, WorkflowState.FAILED, {"error": worker_result["error"]})
        
        error_msg = worker_result["error"]
        if "timed out" in error_msg.lower() or "502" in error_msg:
            friendly_msg = "Sorry, the AI is taking too long to respond. Please try again with a simpler request."
        else:
            friendly_msg = f"Sorry, I ran into an issue: {error_msg}"
        
        # Save error response as assistant message
        ast_msg = ConversationMessage(
            conversation_id=session.id,
            user_id=current_user.id,
            workflow_run_id=workflow.id,
            role="assistant",
            content={"text": friendly_msg, "error": True}
        )
        db.add(ast_msg)
        await db.commit()
        
        return AgentChatResponse(
            workflow_id=workflow.id,
            conversation_id=session.id,
            status="failed",
            message=friendly_msg
        )
        
    # 6. Verification Layer
    is_mutation = worker_result.get("requires_confirmation", False)
    
    if is_mutation:
        verify = verification_layer.verify_action(str(current_user.id), worker_result)
        if not verify["is_safe"]:
            workflow = await state_machine.transition_state(workflow.id, WorkflowState.FAILED, {"error": verify.get("error")})
            raise HTTPException(status_code=403, detail=verify.get("error"))
            
        workflow = await state_machine.transition_state(
            workflow.id, 
            WorkflowState.PLAN_CREATED, 
            {"proposed_actions": worker_result, "approval_status": "pending"}
        )
        
        response_text = worker_result.get("explanation", "I need your approval to proceed.")
        
        # Save assistant message to PostgreSQL
        ast_msg = ConversationMessage(
            conversation_id=session.id,
            user_id=current_user.id,
            workflow_run_id=workflow.id,
            role="assistant",
            content={"text": response_text, "tool_call": worker_result}
        )
        db.add(ast_msg)
        await db.commit()
        await db.refresh(ast_msg)
        
        # Store assistant message in Pinecone (background)
        background_tasks.add_task(
            chat_history.store_message,
            message_id=str(ast_msg.id),
            user_id=str(current_user.id),
            conversation_id=str(session.id),
            role="assistant",
            text=response_text,
            metadata_extra={"has_tool_call": True, "tool_name": worker_result.get("tool_name", "")},
        )
        
        return AgentChatResponse(
            workflow_id=workflow.id,
            conversation_id=session.id,
            status="proposed",
            message=worker_result.get("explanation", "Please confirm the action."),
            tool_calls=[worker_result]
        )
    
    # Auto-approved / Execution
    workflow = await state_machine.transition_state(workflow.id, WorkflowState.EXECUTING)
    
    # Extract memory in background
    background_tasks.add_task(
        memory_service.extract_and_store_memories,
        current_user.id, session.id, request.message, worker_result.get("explanation", "")
    )
    
    workflow = await state_machine.transition_state(workflow.id, WorkflowState.COMPLETED, {"result": worker_result})
    
    response_text = worker_result.get("explanation", "Done.")
    
    ast_msg = ConversationMessage(
        conversation_id=session.id,
        user_id=current_user.id,
        workflow_run_id=workflow.id,
        role="assistant",
        content={"text": response_text}
    )
    db.add(ast_msg)
    await db.commit()
    await db.refresh(ast_msg)
    
    # Store assistant message in Pinecone (background)
    background_tasks.add_task(
        chat_history.store_message,
        message_id=str(ast_msg.id),
        user_id=str(current_user.id),
        conversation_id=str(session.id),
        role="assistant",
        text=response_text,
    )
    
    return AgentChatResponse(
        workflow_id=workflow.id,
        conversation_id=session.id,
        status="completed",
        message=response_text
    )


@router.post("/approve/{workflow_id}", response_model=AgentChatResponse)
async def agent_approve(
    workflow_id: UUID,
    request: AgentApprovalRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    state_machine: deps.StateMachine = Depends(deps.get_state_machine),
    planner_worker: deps.PlannerChangeWorker = Depends(deps.get_planner_worker),
    memory_service: deps.MemoryService = Depends(deps.get_memory_service),
    chat_history: ChatHistoryService = Depends(deps.get_chat_history_service),
):
    """Execute a proposed action after user confirmation."""
    workflow = await state_machine.get_workflow(workflow_id)
    if not workflow or workflow.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    if workflow.state != WorkflowState.PLAN_CREATED.value:
        raise HTTPException(status_code=400, detail="Workflow is not awaiting approval")
        
    if not request.approved:
        workflow = await state_machine.transition_state(workflow.id, WorkflowState.COMPLETED, {"approval_status": "rejected"})
        
        rejection_msg = "Action cancelled."
        
        # Record AI Recommendation rejection for analytics
        rec = AIRecommendation(
            user_id=current_user.id,
            kind=workflow.proposed_actions.get("tool_name", "unknown"),
            scope="chat",
            title=workflow.proposed_actions.get("explanation", "Agent proposal"),
            status="rejected"
        )
        db.add(rec)
        await db.flush()
        
        outcome = RecommendationOutcome(
            recommendation_id=rec.id,
            user_id=current_user.id,
            decision="rejected"
        )
        db.add(outcome)
        
        ast_msg = ConversationMessage(
            conversation_id=workflow.conversation_id,
            user_id=current_user.id,
            workflow_run_id=workflow.id,
            role="assistant",
            content={"text": rejection_msg}
        )
        db.add(ast_msg)
        await db.commit()
        await db.refresh(ast_msg)
        
        background_tasks.add_task(
            chat_history.store_message,
            message_id=str(ast_msg.id),
            user_id=str(current_user.id),
            conversation_id=str(workflow.conversation_id),
            role="assistant",
            text=rejection_msg,
        )
        
        return AgentChatResponse(
            workflow_id=workflow.id,
            conversation_id=workflow.conversation_id,
            status="completed",
            message=rejection_msg
        )
        
    # Execute
    workflow = await state_machine.transition_state(workflow.id, WorkflowState.EXECUTING, {"approval_status": "approved"})
    
    action = workflow.proposed_actions
    tool_name = action.get("tool_name")
    arguments = action.get("arguments", {})
    
    # Apply overrides if provided by the user
    if request.overrides:
        arguments.update(request.overrides)
    
    # Execute the actual mutation using MCP 
    tool_result = await planner_worker.execute_tool(tool_name, arguments)
    
    if "error" in tool_result:
        error_msg = tool_result["error"]
        workflow = await state_machine.transition_state(workflow.id, WorkflowState.FAILED, {"error": error_msg})
        
        fail_msg = f"Sorry, I couldn't complete that action. Error: {error_msg}"
        ast_msg = ConversationMessage(
            conversation_id=workflow.conversation_id,
            user_id=current_user.id,
            workflow_run_id=workflow.id,
            role="assistant",
            content={"text": fail_msg}
        )
        db.add(ast_msg)
        await db.commit()
        await db.refresh(ast_msg)
        
        background_tasks.add_task(
            chat_history.store_message,
            message_id=str(ast_msg.id),
            user_id=str(current_user.id),
            conversation_id=str(workflow.conversation_id),
            role="assistant",
            text=fail_msg,
        )
        
        return AgentChatResponse(
            workflow_id=workflow.id,
            conversation_id=workflow.conversation_id,
            status="completed",
            message=fail_msg
        )
        
    workflow = await state_machine.transition_state(workflow.id, WorkflowState.COMPLETED, {"result": tool_result})
    
    success_msg = f"Successfully executed: {action.get('explanation', tool_name)}"
    
    # Record AI Recommendation acceptance for analytics
    rec = AIRecommendation(
        user_id=current_user.id,
        kind=action.get("tool_name", "unknown"),
        scope="chat",
        title=action.get("explanation", "Agent proposal"),
        status="approved"
    )
    db.add(rec)
    await db.flush()
    
    outcome = RecommendationOutcome(
        recommendation_id=rec.id,
        user_id=current_user.id,
        decision="accepted"
    )
    db.add(outcome)

    ast_msg = ConversationMessage(
        conversation_id=workflow.conversation_id,
        user_id=current_user.id,
        workflow_run_id=workflow.id,
        role="assistant",
        content={"text": success_msg}
    )
    db.add(ast_msg)
    await db.commit()
    await db.refresh(ast_msg)
    
    background_tasks.add_task(
        chat_history.store_message,
        message_id=str(ast_msg.id),
        user_id=str(current_user.id),
        conversation_id=str(workflow.conversation_id),
        role="assistant",
        text=success_msg,
    )
    
    return AgentChatResponse(
        workflow_id=workflow.id,
        conversation_id=workflow.conversation_id,
        status="completed",
        message=success_msg,
        extra_data=tool_result if isinstance(tool_result, dict) else None
    )


@router.get("/conversations", response_model=List[ConversationSessionOut])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """List all conversation sessions for the current user, most recent first."""
    query = select(ConversationSession).where(ConversationSession.user_id == current_user.id).order_by(ConversationSession.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/conversations/recent")
async def get_recent_conversation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Get the most recent conversation and its messages.
    Used by the frontend to restore chat history on panel load.
    """
    query = (
        select(ConversationSession)
        .where(ConversationSession.user_id == current_user.id)
        .order_by(ConversationSession.created_at.desc())
        .limit(1)
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        return {"conversation": None, "messages": []}
    
    msg_query = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == session.id)
        .order_by(ConversationMessage.created_at.asc())
    )
    msg_result = await db.execute(msg_query)
    messages = msg_result.scalars().all()
    
    return {
        "conversation": {
            "id": str(session.id),
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        },
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
    }


@router.get("/conversations/{session_id}/messages", response_model=List[ConversationMessageOut])
async def get_messages(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """Get all messages for a specific conversation session."""
    session = await db.get(ConversationSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    query = select(ConversationMessage).where(ConversationMessage.conversation_id == session_id).order_by(ConversationMessage.created_at.asc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/chat/search")
async def search_chat_history(
    q: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    chat_history: ChatHistoryService = Depends(deps.get_chat_history_service),
):
    """Semantic search over the user's chat history using Pinecone."""
    results = await chat_history.search_chat_history(
        user_id=str(current_user.id),
        query=q,
        limit=limit,
    )
    return {"results": results}
