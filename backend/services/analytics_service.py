from typing import Dict, Any, List, Optional
from backend.db.repositories.analytics import AnalyticsRepository
from backend.core.cache import CacheProvider

class AnalyticsService:
    def __init__(
        self, 
        analytics_repo: AnalyticsRepository, 
        cache_provider: Optional[CacheProvider] = None,
        cache_ttl: int = 300
    ):
        self.analytics_repo = analytics_repo
        self.cache = cache_provider
        self.ttl = cache_ttl

    async def _get_cached_or_fetch(self, cache_key: str, fetch_func):
        if self.cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
                
        data = await fetch_func()
        
        if self.cache:
            await self.cache.set(cache_key, data, self.ttl)
            
        return data

    async def get_overview(self, user_id: str = "global") -> Dict[str, Any]:
        async def fetch():
            rows = await self.analytics_repo.get_daily_activity_stats(user_id)
            
            trends = []
            for r in rows:
                trends.append({
                    "date": r.date,
                    "total_activities": r.total_activities,
                    "completed": r.completed,
                    "not_done": r.not_done,
                    "partial": r.partial,
                    "rescheduled": r.rescheduled,
                    "completion_rate": r.completion_rate
                })
                
            reason_rows = await self.analytics_repo.get_missed_reasons_daily(user_id)
            reasons = [{"name": r.reason_name or "Unknown", "value": r.count} for r in reason_rows]

            total_completed = sum(t["completed"] for t in trends)
            total_tasks = sum(t["total_activities"] for t in trends)
            overall_rate = total_completed / total_tasks if total_tasks > 0 else 0

            return {
                "trends": trends,
                "top_missed_reasons": reasons,
                "kpis": {
                    "completion_rate": overall_rate,
                    "total_completed": total_completed,
                    "total_tasks": total_tasks
                }
            }
            
        return await self._get_cached_or_fetch(f"analytics:overview:{user_id}", fetch)

    async def get_time_patterns(self, user_id: str) -> Dict[str, Any]:
        async def fetch():
            time_rows = await self.analytics_repo.get_time_block_completion(user_id)
            time_blocks = [{"time_bucket": r.time_bucket, "completion_rate": r.completion_rate, "total_activities": r.total_activities} for r in time_rows]

            wd_rows = await self.analytics_repo.get_weekday_completion(user_id)
            weekdays = [{"weekday": r.weekday, "completion_rate": r.completion_rate} for r in wd_rows]
            
            return {
                "time_blocks": time_blocks,
                "weekdays": weekdays
            }
            
        return await self._get_cached_or_fetch(f"analytics:time_patterns:{user_id}", fetch)

    async def get_calendar_conflicts(self, user_id: str = "global") -> List[Dict[str, Any]]:
        async def fetch():
            rows = await self.analytics_repo.get_calendar_conflicts(user_id)
            return [
                {
                    "date": r.date,
                    "activities_conflicted": r.activities_conflicted,
                    "conflicted_completion_rate": r.conflicted_completion_rate,
                    "non_conflicted_completion_rate": r.non_conflicted_completion_rate
                } for r in rows
            ]
            
        return await self._get_cached_or_fetch(f"analytics:calendar_conflicts:{user_id}", fetch)

    async def get_focus_metrics(self, user_id: str = "global") -> List[Dict[str, Any]]:
        async def fetch():
            rows = await self.analytics_repo.get_focus_metrics(user_id)
            return [
                {
                    "activity_id": r.activity_id,
                    "focus_ratio": r.focus_ratio,
                    "blocked_attempts": r.blocked_attempts
                } for r in rows
            ]
            
        return await self._get_cached_or_fetch(f"analytics:focus_metrics:{user_id}", fetch)

    async def get_ai_effectiveness(self, user_id: str = "global") -> List[Dict[str, Any]]:
        async def fetch():
            rows = await self.analytics_repo.get_recommendation_effect(user_id)
            return [
                {
                    "recommendation_id": r.recommendation_id,
                    "decision": r.decision,
                    "title": r.title,
                    "date": r.date
                } for r in rows
            ]
            
        return await self._get_cached_or_fetch(f"analytics:ai_effectiveness:{user_id}", fetch)
