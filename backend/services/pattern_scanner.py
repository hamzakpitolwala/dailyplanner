import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from backend.db.models.core import Task, TaskCheckin
from backend.db.models.integrations import ExternalSyncedEvent

logger = logging.getLogger(__name__)

class PatternEvent:
    def __init__(self, pattern_type: str, activity_ids: List[str], time_window: str, evidence: Dict[str, Any]):
        self.pattern_type = pattern_type
        self.activity_ids = activity_ids
        self.time_window = time_window
        self.evidence = evidence

    def to_dict(self) -> dict:
        return {
            "pattern_type": self.pattern_type,
            "activity_ids": self.activity_ids,
            "time_window": self.time_window,
            "evidence": self.evidence
        }


class PatternRule(ABC):
    """Strategy interface for pattern scanning rules."""
    @abstractmethod
    async def evaluate(self, user_id: str, db: AsyncSession, start_date: date, end_date: date) -> List[PatternEvent]:
        pass


class RepeatedMissesRule(PatternRule):
    """Detects activities that are repeatedly missed in a specific time window."""
    async def evaluate(self, user_id: str, db: AsyncSession, start_date: date, end_date: date) -> List[PatternEvent]:
        logger.info(f"Evaluating RepeatedMissesRule for user {user_id} between {start_date} and {end_date}")
        events = []
        # A simple implementation fetching recent checkins
        # In a real scenario, this would group by time window and count misses
        query = select(Task, TaskCheckin).join(
            TaskCheckin, Task.id == TaskCheckin.task_id
        ).where(
            Task.user_id == user_id,
            TaskCheckin.status.in_(["not_done", "partial"])
        )
        
        result = await db.execute(query)
        missed_tasks = result.all()
        
        # Dictionary to count misses by title/time
        miss_counts = {}
        for task, checkin in missed_tasks:
            key = f"{task.title}_{task.start_time.hour if task.start_time else 'none'}"
            if key not in miss_counts:
                miss_counts[key] = {"count": 0, "task_ids": set(), "time": f"{task.start_time.hour if task.start_time else '00'}:00"}
            miss_counts[key]["count"] += 1
            miss_counts[key]["task_ids"].add(str(task.id))
            
        for key, data in miss_counts.items():
            if data["count"] >= 3:
                logger.debug(f"Detected repeated miss for {key} with {data['count']} misses")
                events.append(PatternEvent(
                    pattern_type="repeated_miss_time_window",
                    activity_ids=list(data["task_ids"]),
                    time_window=data["time"],
                    evidence={"count": data["count"]}
                ))
        return events


class OverloadDayRule(PatternRule):
    """Detects days with excessive planned work and low completion rate."""
    async def evaluate(self, user_id: str, db: AsyncSession, start_date: date, end_date: date) -> List[PatternEvent]:
        logger.info(f"Evaluating OverloadDayRule for user {user_id}")
        events = []
        # Simplistic implementation: just returns empty or logic here.
        # Can be expanded later.
        return events


class CalendarConflictRule(PatternRule):
    """Detects misses that correlate with calendar events overlapping planner blocks."""
    async def evaluate(self, user_id: str, db: AsyncSession, start_date: date, end_date: date) -> List[PatternEvent]:
        logger.info(f"Evaluating CalendarConflictRule for user {user_id}")
        events = []
        # Simplistic implementation
        return events


class PatternScannerService:
    """Context for PatternScanner that applies a list of rules."""
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rules: List[PatternRule] = [
            RepeatedMissesRule(),
            OverloadDayRule(),
            CalendarConflictRule()
        ]

    async def scan(self, user_id: str, period_days: int = 7) -> List[PatternEvent]:
        logger.info(f"Starting pattern scan for user {user_id} over last {period_days} days")
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)
        
        all_events = []
        for rule in self.rules:
            try:
                events = await rule.evaluate(user_id, self.db, start_date, end_date)
                all_events.extend(events)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.__class__.__name__}: {e}", exc_info=True)
                
        logger.info(f"Completed pattern scan. Found {len(all_events)} events.")
        return all_events
