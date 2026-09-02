import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from backend.mcp_server import mcp
from backend.db.database import SessionLocal
from backend.db.repositories.task import TaskRepository, CategoryRepository
from backend.db.repositories.user import UserRepository
from backend.db.repositories.fixed_block import FixedBlockRepository
from backend.db.repositories.analytics import AnalyticsRepository
from backend.services.task_service import TaskService
from backend.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

async def _get_services():
    db = SessionLocal()
    task_repo = TaskRepository(db)
    category_repo = CategoryRepository(db)
    user_repo = UserRepository(db)
    fixed_block_repo = FixedBlockRepository(db)
    analytics_repo = AnalyticsRepository(db)
    
    task_service = TaskService(task_repo=task_repo, category_repo=category_repo, user_repo=user_repo)
    analytics_service = AnalyticsService(analytics_repo=analytics_repo)
    return task_service, analytics_service, fixed_block_repo, db

@mcp.tool()
async def get_tasks(user_id: str, date_str: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get tasks for the user, optionally filtered by date (YYYY-MM-DD) and status."""
    task_service, _, _, db = await _get_services()
    try:
        from datetime import datetime, time, timezone
        
        start_of_day = None
        end_of_day = None
        if date_str:
            dt = datetime.fromisoformat(date_str)
            start_of_day = datetime.combine(dt.date(), time(0, 0, 0), tzinfo=timezone.utc)
            end_of_day = datetime.combine(dt.date(), time(23, 59, 59), tzinfo=timezone.utc)
            
        tasks = await task_service.list_tasks(
            user_id=UUID(user_id),
            start_time_gte=start_of_day,
            due_date_lte=end_of_day,
            status=status
        )
        return [{
            "id": str(t.id),
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "start_time": t.start_time.isoformat() if t.start_time else None,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "category": t.category.name if t.category else None
        } for t in tasks]
    finally:
        await db.close()

@mcp.tool()
async def get_schedule(user_id: str, date_str: str) -> Dict[str, Any]:
    """Get the full schedule for a day including tasks and fixed blocks."""
    task_service, _, fixed_block_repo, db = await _get_services()
    try:
        from datetime import datetime, time, timezone
        dt = datetime.fromisoformat(date_str)
        start_of_day = datetime.combine(dt.date(), time(0, 0, 0), tzinfo=timezone.utc)
        end_of_day = datetime.combine(dt.date(), time(23, 59, 59), tzinfo=timezone.utc)
        
        tasks = await task_service.list_tasks(user_id=UUID(user_id), start_time_gte=start_of_day, due_date_lte=end_of_day)
        blocks = await fixed_block_repo.list_fixed_blocks(UUID(user_id))
        
        weekday = dt.weekday()
        day_blocks = [b for b in blocks if weekday in b.days_of_week]
        
        return {
            "date": date_str,
            "tasks": [{
                "id": str(t.id),
                "title": t.title,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            } for t in tasks],
            "fixed_blocks": [{
                "id": str(b.id),
                "name": b.name,
                "start_time": b.start_time,
                "end_time": b.end_time
            } for b in day_blocks]
        }
    finally:
        await db.close()

@mcp.tool()
async def get_today_summary(user_id: str) -> Dict[str, Any]:
    """Get counts of tasks for today by status."""
    task_service, _, _, db = await _get_services()
    try:
        from datetime import datetime, time, timezone
        now = datetime.now(timezone.utc)
        start_of_day = datetime.combine(now.date(), time(0, 0, 0), tzinfo=timezone.utc)
        end_of_day = datetime.combine(now.date(), time(23, 59, 59), tzinfo=timezone.utc)
        
        tasks = await task_service.list_tasks(user_id=UUID(user_id), start_time_gte=start_of_day, due_date_lte=end_of_day)
        
        summary = {"completed": 0, "pending": 0, "missed": 0, "total": len(tasks)}
        for t in tasks:
            if t.status in summary:
                summary[t.status] += 1
        return summary
    finally:
        await db.close()

@mcp.tool()
async def get_overdue_tasks(user_id: str) -> List[Dict[str, Any]]:
    """Get tasks that are past their due date and not completed."""
    task_service, _, _, db = await _get_services()
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        tasks = await task_service.list_tasks(user_id=UUID(user_id), status="pending")
        overdue = [t for t in tasks if t.due_date and t.due_date < now]
        
        return [{
            "id": str(t.id),
            "title": t.title,
            "due_date": t.due_date.isoformat(),
        } for t in overdue]
    finally:
        await db.close()

@mcp.tool()
async def find_schedule_conflicts(user_id: str, date_str: str) -> List[Dict[str, Any]]:
    """Find overlapping tasks and fixed blocks for a specific date."""
    # Simplified version - could be expanded based on exact overlap logic
    schedule = await get_schedule(user_id, date_str)
    return {"message": "Conflict detection not fully implemented yet, returning raw schedule", "schedule": schedule}

@mcp.tool()
async def get_analytics(user_id: str, period_start: str, period_end: str) -> Dict[str, Any]:
    """Get analytics for a specific time period."""
    _, analytics_service, _, db = await _get_services()
    try:
        overview = await analytics_service.get_overview(user_id)
        time_patterns = await analytics_service.get_time_patterns(user_id)
        focus = await analytics_service.get_focus_metrics(user_id)
        return {
            "overview": overview,
            "time_patterns": time_patterns,
            "focus_metrics": focus
        }
    finally:
        await db.close()
