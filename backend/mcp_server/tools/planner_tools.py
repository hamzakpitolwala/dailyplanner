import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from backend.mcp_server import mcp
from backend.db.database import SessionLocal
from backend.db.repositories.task import TaskRepository, CategoryRepository
from backend.db.repositories.user import UserRepository
from backend.services.task_service import TaskService
from backend.schemas.core_schema import TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


async def _resolve_task(service, user_id: str, identifier: str):
    """ resolve task."""
    from uuid import UUID
    try:
        task_id = UUID(identifier.strip())
        return await service.get_task(UUID(user_id), task_id)
    except ValueError:
        # Not a UUID, search by title
        tasks = await service.list_tasks(UUID(user_id))
        identifier_lower = identifier.strip().lower()
        
        matches = [t for t in tasks if t.title.lower() == identifier_lower]
        
        # Prefer pending tasks if there are multiple matches
        pending_matches = [t for t in matches if t.status != "completed"]
        
        if pending_matches:
            return pending_matches[0]
        elif matches:
            return matches[0]
        
        return None

async def _get_task_service():
    """ get task service."""
    db = SessionLocal()
    task_repo = TaskRepository(db)
    category_repo = CategoryRepository(db)
    user_repo = UserRepository(db)
    return TaskService(task_repo=task_repo, category_repo=category_repo, user_repo=user_repo), db

@mcp.tool()
async def create_task(user_id: str, title: str, start_time: Optional[str] = None, end_time: Optional[str] = None, priority: int = 1, category_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a new task in the planner."""
    service, db = await _get_task_service()
    try:
        data = TaskCreate(
            title=title,
            start_time=datetime.fromisoformat(start_time.replace("Z", "+00:00")) if start_time else None,
            due_date=datetime.fromisoformat(end_time.replace("Z", "+00:00")) if end_time else None,
            priority=priority,
            category_id=UUID(category_id) if category_id else None
        )
        task = await service.create_task(UUID(user_id), data)
        return {
            "id": str(task.id),
            "title": task.title,
            "status": task.status,
            "start_time": task.start_time.isoformat() if task.start_time else None,
            "due_date": task.due_date.isoformat() if task.due_date else None,
        }
    finally:
        await db.close()

@mcp.tool()
async def update_task(user_id: str, task_id: str, title: Optional[str] = None, priority: Optional[int] = None) -> Dict[str, Any]:
    """Update an existing task's title or priority."""
    service, db = await _get_task_service()
    try:
        task = await _resolve_task(service, user_id, task_id)
        if not task:
            return {"error": "Task not found"}
        
        data = TaskUpdate()
        if title is not None:
            data.title = title
        if priority is not None:
            data.priority = priority
            
        updated_task = await service.update_task(task, data)
        return {
            "id": str(updated_task.id),
            "title": updated_task.title,
            "priority": updated_task.priority,
        }
    finally:
        await db.close()

@mcp.tool()
async def delete_task(user_id: str, task_id: str) -> Dict[str, Any]:
    """Delete a task from the planner."""
    service, db = await _get_task_service()
    try:
        task = await _resolve_task(service, user_id, task_id)
        if not task:
            return {"error": "Task not found"}
        await service.delete_task(task)
        return {"success": True, "deleted_task_id": task_id}
    finally:
        await db.close()

@mcp.tool()
async def complete_task(user_id: str, task_id: str) -> Dict[str, Any]:
    """Mark a task as completed."""
    service, db = await _get_task_service()
    try:
        task = await _resolve_task(service, user_id, task_id)
        if not task:
            return {"error": "Task not found"}
            
        data = TaskUpdate(status="completed")
        updated_task = await service.update_task(task, data)
        return {"success": True, "id": str(updated_task.id), "status": updated_task.status}
    finally:
        await db.close()

@mcp.tool()
async def move_task(user_id: str, task_id: str, new_start_time: str, new_end_time: str) -> Dict[str, Any]:
    """Move a task to a new time slot."""
    service, db = await _get_task_service()
    try:
        task = await _resolve_task(service, user_id, task_id)
        if not task:
            return {"error": "Task not found"}
            
        data = TaskUpdate(
            start_time=datetime.fromisoformat(new_start_time.replace("Z", "+00:00")),
            due_date=datetime.fromisoformat(new_end_time.replace("Z", "+00:00"))
        )
        updated_task = await service.update_task(task, data)
        return {
            "id": str(updated_task.id),
            "title": updated_task.title,
            "start_time": updated_task.start_time.isoformat() if updated_task.start_time else None,
            "due_date": updated_task.due_date.isoformat() if updated_task.due_date else None,
        }
    finally:
        await db.close()

@mcp.tool()
async def reschedule_task(user_id: str, task_id: str, new_date: str) -> Dict[str, Any]:
    """Reschedule a task to a completely new date."""
    service, db = await _get_task_service()
    try:
        task = await _resolve_task(service, user_id, task_id)
        if not task:
            return {"error": "Task not found"}
            
        # For simplicity, if it's an all day task, we set the due_date to end of new_date
        # If it has a start time, we keep the time but change the date
        from datetime import datetime, time, timedelta
        target_date = datetime.fromisoformat(new_date[:10])
        
        data = TaskUpdate()
        if task.start_time:
            # maintain duration
            duration = (task.due_date - task.start_time) if task.due_date else timedelta(hours=1)
            new_start = datetime.combine(target_date.date(), task.start_time.time(), tzinfo=task.start_time.tzinfo)
            data.start_time = new_start
            data.due_date = new_start + duration
        else:
            # end of day
            data.due_date = datetime.combine(target_date.date(), time(23, 59, 59), tzinfo=task.due_date.tzinfo if task.due_date else None)
            
        updated_task = await service.update_task(task, data)
        return {
            "id": str(updated_task.id),
            "start_time": updated_task.start_time.isoformat() if updated_task.start_time else None,
            "due_date": updated_task.due_date.isoformat() if updated_task.due_date else None,
        }
    finally:
        await db.close()

@mcp.tool()
async def add_subtask(user_id: str, task_id: str, title: str) -> Dict[str, Any]:
    """Add a subtask to an existing task."""
    service, db = await _get_task_service()
    try:
        from backend.schemas.task_schema import ActivitySubtaskCreate
        task = await _resolve_task(service, user_id, task_id)
        if not task:
            return {"error": "Task not found"}
            
        sub_data = ActivitySubtaskCreate(title=title)
        subtask = await service.create_subtask(task, sub_data)
        return {
            "id": str(subtask.id),
            "task_id": str(subtask.task_id),
            "title": subtask.title,
            "is_completed": bool(subtask.is_completed)
        }
    finally:
        await db.close()
