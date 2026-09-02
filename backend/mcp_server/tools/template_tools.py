import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from backend.mcp_server import mcp
from backend.db.database import SessionLocal
from backend.db.repositories.template import TemplateRepository, TemplateTaskRepository
from backend.db.repositories.task import TaskRepository
from backend.services.template_service import TemplateService

logger = logging.getLogger(__name__)

async def _get_template_service():
    db = SessionLocal()
    template_repo = TemplateRepository(db)
    template_task_repo = TemplateTaskRepository(db)
    task_repo = TaskRepository(db)
    return TemplateService(template_repo=template_repo, template_task_repo=template_task_repo, task_repo=task_repo), db

@mcp.tool()
async def list_templates(user_id: str) -> List[Dict[str, Any]]:
    """List all available templates for the user."""
    service, db = await _get_template_service()
    try:
        templates = await service.list_templates(UUID(user_id))
        return [{
            "id": str(t.id),
            "name": t.name,
            "description": t.description,
            "day_type": t.day_type,
            "is_active": t.is_active
        } for t in templates]
    finally:
        await db.close()

@mcp.tool()
async def apply_template(user_id: str, template_id: str, target_date: str, tz_offset: int = 0) -> Dict[str, Any]:
    """Apply a template to a specific date."""
    service, db = await _get_template_service()
    try:
        from datetime import datetime
        start_date = datetime.fromisoformat(target_date.replace("Z", "+00:00"))
        
        try:
            valid_user_id = UUID(user_id)
            valid_template_id = UUID(template_id)
        except ValueError:
            return {"error": "Invalid UUID format for user_id or template_id. Please use list_templates to find the correct template_id."}

        tasks = await service.instantiate_template_to_tasks(
            user_id=valid_user_id,
            template_id=valid_template_id,
            start_date=start_date,
            tz_offset=tz_offset
        )
        return {
            "success": True,
            "tasks_created": len(tasks),
            "tasks": [{"id": str(t.id), "title": t.title} for t in tasks]
        }
    finally:
        await db.close()

@mcp.tool()
async def create_template(user_id: str, name: str, description: str = "", tasks: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new template with predefined tasks. Tasks should be a list of objects with title, description, priority, target_time (HH:MM:SS), duration_minutes."""
    if tasks is None:
        tasks = []
        
    service, db = await _get_template_service()
    try:
        from backend.schemas.template_schema import PlannerTemplateCreate, TemplateTaskCreate
        from datetime import time
        
        template_tasks = []
        for t in tasks:
            target_time_val = None
            if "target_time" in t and t["target_time"]:
                try:
                    time_parts = str(t["target_time"]).split(":")
                    if len(time_parts) >= 2:
                        target_time_val = time(int(time_parts[0]), int(time_parts[1]))
                except ValueError:
                    pass
                    
            template_tasks.append(
                TemplateTaskCreate(
                    title=t.get("title", "New Task"),
                    description=t.get("description"),
                    priority=int(t.get("priority", 1)),
                    duration_minutes=int(t.get("duration_minutes", 60)),
                    target_time=target_time_val
                )
            )
            
        data = PlannerTemplateCreate(
            name=name,
            description=description,
            template_tasks=template_tasks
        )
        
        template = await service.create_template(UUID(user_id), data)
        return {
            "id": str(template.id),
            "name": template.name,
            "tasks_count": len(template.template_tasks)
        }
    finally:
        await db.close()

@mcp.tool()
async def add_task_to_template(user_id: str, template_id: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Add new tasks to an existing template. Tasks should be a list of objects with title, description, priority, target_time (HH:MM:SS), duration_minutes."""
    if not tasks:
        return {"error": "No tasks provided."}
        
    service, db = await _get_template_service()
    try:
        from backend.schemas.template_schema import TemplateTaskCreate
        from datetime import time
        
        try:
            valid_user_id = UUID(user_id)
            valid_template_id = UUID(template_id)
        except ValueError:
            return {"error": "Invalid UUID format for user_id or template_id."}
            
        template = await service.get_template(valid_user_id, valid_template_id)
        if not template:
            return {"error": "Template not found."}
            
        added_count = 0
        for t in tasks:
            target_time_val = None
            if "target_time" in t and t["target_time"]:
                try:
                    time_parts = str(t["target_time"]).split(":")
                    if len(time_parts) >= 2:
                        target_time_val = time(int(time_parts[0]), int(time_parts[1]))
                except ValueError:
                    pass
                    
            task_data = TemplateTaskCreate(
                title=t.get("title", "New Task"),
                description=t.get("description"),
                priority=int(t.get("priority", 1)),
                duration_minutes=int(t.get("duration_minutes", 60)),
                target_time=target_time_val
            )
            await service.create_template_task(template, task_data)
            added_count += 1
            
        return {
            "success": True,
            "message": f"Added {added_count} task(s) to template '{template.name}'."
        }
    finally:
        await db.close()

async def _resolve_template_task(service, user_id: UUID, template_name: str, task_name: str, target_time: Optional[str] = None):
    template = await service.get_template_by_name(user_id, template_name)
    if not template:
        return None, f"Template '{template_name}' not found."
    
    if task_name.lower() == "all":
        return template.template_tasks, None

    matching_tasks = [t for t in template.template_tasks if t.title.lower() == task_name.lower()]
    
    if not matching_tasks:
        return None, f"Task '{task_name}' not found in template '{template_name}'."
        
    if len(matching_tasks) == 1:
        return matching_tasks[0], None
        
    if target_time:
        for t in matching_tasks:
            if t.target_time and t.target_time.strftime("%H:%M") == target_time:
                return t, None
        return None, f"Found multiple tasks named '{task_name}', but none matched target_time '{target_time}'. Please verify the time."
        
    return None, f"Found {len(matching_tasks)} tasks named '{task_name}'. Please specify target_time (HH:MM) to disambiguate."

@mcp.tool()
async def read_task_in_template(user_id: str, template_name: str, task_name: str, target_time: Optional[str] = None) -> Dict[str, Any]:
    """Read a task from a template, highlighting it in the UI."""
    service, db = await _get_template_service()
    try:
        task, error = await _resolve_template_task(service, UUID(user_id), template_name, task_name, target_time)
        if error:
            return {"error": error}
        if isinstance(task, list):
            return {"error": "read_task_in_template does not support 'all' tasks."}
            
        return {
            "success": True,
            "task": {
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "target_time": task.target_time.strftime("%H:%M") if hasattr(task.target_time, "strftime") else str(task.target_time)[:5] if task.target_time else None,
                "duration_minutes": task.duration_minutes
            },
            "ui_action": "highlight_template_task",
            "highlight_task_id": str(task.id)
        }
    finally:
        await db.close()

@mcp.tool()
async def update_task_in_template(user_id: str, template_name: str, task_name: str, target_time: Optional[str] = None, new_title: Optional[str] = None, new_description: Optional[str] = None, new_priority: Optional[int] = None, new_target_time: Optional[str] = None, new_duration_minutes: Optional[int] = None, affect_all: bool = False) -> Dict[str, Any]:
    """Update a task (or all tasks if task_name='all' or affect_all=True) in a template."""
    service, db = await _get_template_service()
    try:
        from backend.schemas.template_schema import TemplateTaskUpdate
        from datetime import time
        
        if affect_all:
            task_name = "all"
            
        task_or_tasks, error = await _resolve_template_task(service, UUID(user_id), template_name, task_name, target_time)
        if error:
            return {"error": error}
            
        tasks_to_update = task_or_tasks if isinstance(task_or_tasks, list) else [task_or_tasks]
        
        update_data = {}
        if new_title is not None: update_data["title"] = new_title
        if new_description is not None: update_data["description"] = new_description
        if new_priority is not None: update_data["priority"] = new_priority
        if new_duration_minutes is not None: update_data["duration_minutes"] = new_duration_minutes
        if new_target_time is not None:
            time_parts = new_target_time.split(":")
            update_data["target_time"] = time(int(time_parts[0]), int(time_parts[1]))
            
        if not update_data:
            return {"error": "No update fields provided."}
            
        updated_count = 0
        for t in tasks_to_update:
            await service.update_template_task(t, TemplateTaskUpdate(**update_data))
            updated_count += 1
            
        return {"success": True, "message": f"Updated {updated_count} task(s)."}
    finally:
        await db.close()

@mcp.tool()
async def delete_task_from_template(user_id: str, template_name: str, task_name: str, target_time: Optional[str] = None, affect_all: bool = False) -> Dict[str, Any]:
    """Delete a task (or all tasks if task_name='all' or affect_all=True) from a template."""
    service, db = await _get_template_service()
    try:
        if affect_all:
            task_name = "all"
            
        task_or_tasks, error = await _resolve_template_task(service, UUID(user_id), template_name, task_name, target_time)
        if error:
            return {"error": error}
            
        tasks_to_delete = task_or_tasks if isinstance(task_or_tasks, list) else [task_or_tasks]
        
        deleted_count = 0
        for t in tasks_to_delete:
            await service.delete_template_task(t)
            deleted_count += 1
            
        return {"success": True, "message": f"Deleted {deleted_count} task(s)."}
    finally:
        await db.close()
