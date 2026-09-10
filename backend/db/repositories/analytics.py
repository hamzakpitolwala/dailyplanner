from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Any, List, Dict

class AnalyticsRepository:
    """Analyticsrepository."""
    def __init__(self, db: AsyncSession):
        """  init  ."""
        self.db = db

    async def get_daily_activity_stats(self, user_id: str) -> List[Any]:
        """Get daily activity stats."""
        query = text("""
            SELECT date, total_activities, completed, not_done, partial, rescheduled, completion_rate
            FROM v_daily_activity_stats
            WHERE user_id = :user_id
            ORDER BY date ASC
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        return result.fetchall()

    async def get_missed_reasons_daily(self, user_id: str) -> List[Any]:
        """Get missed reasons daily."""
        query = text("""
            SELECT reason_name, SUM(count) as count
            FROM v_missed_reasons_daily
            WHERE user_id = :user_id
            GROUP BY reason_name
            ORDER BY count DESC
            LIMIT 5
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        return result.fetchall()

    async def get_time_block_completion(self, user_id: str) -> List[Any]:
        """Get time block completion."""
        query = text("""
            SELECT time_bucket, completion_rate, total_activities
            FROM v_time_block_completion
            WHERE user_id = :user_id
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        return result.fetchall()

    async def get_weekday_completion(self, user_id: str) -> List[Any]:
        """Get weekday completion."""
        query = text("""
            SELECT weekday, completion_rate
            FROM v_weekday_completion
            WHERE user_id = :user_id
            ORDER BY weekday
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        return result.fetchall()

    async def get_calendar_conflicts(self, user_id: str) -> List[Any]:
        """Get calendar conflicts."""
        query = text("""
            SELECT date, activities_conflicted, conflicted_completion_rate, non_conflicted_completion_rate
            FROM v_calendar_conflicts
            WHERE user_id = :user_id
            ORDER BY date ASC
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        return result.fetchall()

    async def get_focus_metrics(self, user_id: str) -> List[Any]:
        """Get focus metrics."""
        query = text("""
            SELECT activity_id, focus_ratio, blocked_attempts
            FROM v_focus_metrics
            WHERE user_id = :user_id
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        return result.fetchall()

    async def get_recommendation_effect(self, user_id: str) -> List[Any]:
        """Get recommendation effect."""
        query = text("""
            SELECT recommendation_id, decision, title, date
            FROM v_recommendation_effect
            WHERE user_id = :user_id
            ORDER BY date ASC
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        return result.fetchall()
