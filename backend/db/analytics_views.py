import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

POSTGRES_VIEWS = [
    """
    CREATE OR REPLACE VIEW v_daily_activity_stats AS
    SELECT 
        t.user_id,
        CAST(t.due_date AS DATE) as date,
        COUNT(t.id) as total_activities,
        SUM(CASE WHEN tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) as completed,
        SUM(CASE WHEN tc.status = 'not_done' THEN 1 ELSE 0 END) as not_done,
        SUM(CASE WHEN tc.status = 'partial' THEN 1 ELSE 0 END) as partial,
        SUM(CASE WHEN tc.status = 'rescheduled' THEN 1 ELSE 0 END) as rescheduled,
        CAST(SUM(CASE WHEN tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(t.id), 0) as completion_rate
    FROM tasks t
    LEFT JOIN task_checkins tc ON t.id = tc.task_id
    WHERE t.due_date IS NOT NULL
    GROUP BY t.user_id, CAST(t.due_date AS DATE);
    """,
    """
    CREATE OR REPLACE VIEW v_daily_subtask_stats AS
    SELECT 
        t.user_id,
        CAST(t.due_date AS DATE) as date,
        COUNT(s.id) as total_subtasks,
        SUM(s.is_completed) as completed_subtasks,
        CAST(SUM(s.is_completed) AS FLOAT) / NULLIF(COUNT(s.id), 0) as subtask_completion_rate
    FROM tasks t
    JOIN activity_subtasks s ON t.id = s.task_id
    WHERE t.due_date IS NOT NULL
    GROUP BY t.user_id, CAST(t.due_date AS DATE);
    """,
    """
    CREATE OR REPLACE VIEW v_missed_reasons_daily AS
    SELECT 
        t.user_id,
        CAST(tc.created_at AS DATE) as date,
        tc.missed_reason_id,
        mr.name as reason_name,
        COUNT(tc.id) as count
    FROM task_checkins tc
    LEFT JOIN missed_reasons mr ON tc.missed_reason_id = mr.id
    JOIN tasks t ON tc.task_id = t.id
    WHERE tc.status = 'not_done' AND tc.missed_reason_id IS NOT NULL
    GROUP BY t.user_id, CAST(tc.created_at AS DATE), tc.missed_reason_id, mr.name;
    """,
    """
    CREATE OR REPLACE VIEW v_time_block_completion AS
    SELECT 
        t.user_id,
        CASE 
            WHEN EXTRACT(HOUR FROM t.start_time) BETWEEN 5 AND 11 THEN 'Morning'
            WHEN EXTRACT(HOUR FROM t.start_time) BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN EXTRACT(HOUR FROM t.start_time) BETWEEN 17 AND 21 THEN 'Evening'
            ELSE 'Night'
        END as time_bucket,
        CAST(SUM(CASE WHEN tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(t.id), 0) as completion_rate,
        COUNT(t.id) as total_activities
    FROM tasks t
    LEFT JOIN task_checkins tc ON t.id = tc.task_id
    WHERE t.start_time IS NOT NULL
    GROUP BY 
        t.user_id,
        CASE 
            WHEN EXTRACT(HOUR FROM t.start_time) BETWEEN 5 AND 11 THEN 'Morning'
            WHEN EXTRACT(HOUR FROM t.start_time) BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN EXTRACT(HOUR FROM t.start_time) BETWEEN 17 AND 21 THEN 'Evening'
            ELSE 'Night'
        END;
    """,
    """
    CREATE OR REPLACE VIEW v_weekday_completion AS
    SELECT 
        t.user_id,
        EXTRACT(DOW FROM t.due_date) as weekday,
        CAST(SUM(CASE WHEN tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(t.id), 0) as completion_rate
    FROM tasks t
    LEFT JOIN task_checkins tc ON t.id = tc.task_id
    WHERE t.due_date IS NOT NULL
    GROUP BY t.user_id, EXTRACT(DOW FROM t.due_date);
    """,
    """
    CREATE OR REPLACE VIEW v_calendar_conflicts AS
    SELECT 
        t.user_id,
        CAST(t.due_date AS DATE) as date,
        SUM(CASE WHEN t.external_event_id IS NOT NULL THEN 1 ELSE 0 END) as activities_conflicted,
        CAST(SUM(CASE WHEN t.external_event_id IS NOT NULL AND tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(SUM(CASE WHEN t.external_event_id IS NOT NULL THEN 1 ELSE 0 END), 0) as conflicted_completion_rate,
        CAST(SUM(CASE WHEN t.external_event_id IS NULL AND tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(SUM(CASE WHEN t.external_event_id IS NULL THEN 1 ELSE 0 END), 0) as non_conflicted_completion_rate
    FROM tasks t
    LEFT JOIN task_checkins tc ON t.id = tc.task_id
    WHERE t.due_date IS NOT NULL
    GROUP BY t.user_id, CAST(t.due_date AS DATE);
    """,
    """
    CREATE OR REPLACE VIEW v_focus_metrics AS
    SELECT 
        ms.user_id,
        ms.activity_id,
        CAST(SUM(CASE WHEN se.is_blocked = 0 THEN se.duration_seconds ELSE 0 END) AS FLOAT) / NULLIF(SUM(se.duration_seconds), 0) as focus_ratio,
        SUM(CASE WHEN se.is_blocked = 1 THEN 1 ELSE 0 END) as blocked_attempts
    FROM monitoring_sessions ms
    LEFT JOIN screen_events se ON ms.id = se.session_id
    GROUP BY ms.user_id, ms.activity_id;
    """,
    """
    CREATE OR REPLACE VIEW v_recommendation_effect AS
    SELECT 
        ar.user_id,
        ro.recommendation_id,
        ro.decision,
        ar.title,
        CAST(ro.decided_at AS DATE) as date
    FROM recommendation_outcomes ro
    JOIN ai_recommendations ar ON ro.recommendation_id = ar.id
    WHERE ro.decision = 'accepted';
    """
]

SQLITE_VIEWS = [
    """
    DROP VIEW IF EXISTS v_daily_activity_stats;
    """,
    """
    CREATE VIEW v_daily_activity_stats AS
    SELECT 
        t.user_id,
        date(t.due_date) as date,
        COUNT(t.id) as total_activities,
        SUM(CASE WHEN tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) as completed,
        SUM(CASE WHEN tc.status = 'not_done' THEN 1 ELSE 0 END) as not_done,
        SUM(CASE WHEN tc.status = 'partial' THEN 1 ELSE 0 END) as partial,
        SUM(CASE WHEN tc.status = 'rescheduled' THEN 1 ELSE 0 END) as rescheduled,
        CAST(SUM(CASE WHEN tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(t.id), 0) as completion_rate
    FROM tasks t
    LEFT JOIN task_checkins tc ON t.id = tc.task_id
    WHERE t.due_date IS NOT NULL
    GROUP BY t.user_id, date(t.due_date);
    """,
    """
    DROP VIEW IF EXISTS v_daily_subtask_stats;
    """,
    """
    CREATE VIEW v_daily_subtask_stats AS
    SELECT 
        t.user_id,
        date(t.due_date) as date,
        COUNT(s.id) as total_subtasks,
        SUM(s.is_completed) as completed_subtasks,
        CAST(SUM(s.is_completed) AS FLOAT) / NULLIF(COUNT(s.id), 0) as subtask_completion_rate
    FROM tasks t
    JOIN activity_subtasks s ON t.id = s.task_id
    WHERE t.due_date IS NOT NULL
    GROUP BY t.user_id, date(t.due_date);
    """,
    """
    DROP VIEW IF EXISTS v_missed_reasons_daily;
    """,
    """
    CREATE VIEW v_missed_reasons_daily AS
    SELECT 
        t.user_id,
        date(tc.created_at) as date,
        tc.missed_reason_id,
        mr.name as reason_name,
        COUNT(tc.id) as count
    FROM task_checkins tc
    LEFT JOIN missed_reasons mr ON tc.missed_reason_id = mr.id
    JOIN tasks t ON tc.task_id = t.id
    WHERE tc.status = 'not_done' AND tc.missed_reason_id IS NOT NULL
    GROUP BY t.user_id, date(tc.created_at), tc.missed_reason_id, mr.name;
    """,
    """
    DROP VIEW IF EXISTS v_time_block_completion;
    """,
    """
    CREATE VIEW v_time_block_completion AS
    SELECT 
        t.user_id,
        CASE 
            WHEN CAST(strftime('%H', t.start_time) AS INTEGER) BETWEEN 5 AND 11 THEN 'Morning'
            WHEN CAST(strftime('%H', t.start_time) AS INTEGER) BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN CAST(strftime('%H', t.start_time) AS INTEGER) BETWEEN 17 AND 21 THEN 'Evening'
            ELSE 'Night'
        END as time_bucket,
        CAST(SUM(CASE WHEN tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(t.id), 0) as completion_rate,
        COUNT(t.id) as total_activities
    FROM tasks t
    LEFT JOIN task_checkins tc ON t.id = tc.task_id
    WHERE t.start_time IS NOT NULL
    GROUP BY 
        t.user_id,
        CASE 
            WHEN CAST(strftime('%H', t.start_time) AS INTEGER) BETWEEN 5 AND 11 THEN 'Morning'
            WHEN CAST(strftime('%H', t.start_time) AS INTEGER) BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN CAST(strftime('%H', t.start_time) AS INTEGER) BETWEEN 17 AND 21 THEN 'Evening'
            ELSE 'Night'
        END;
    """,
    """
    DROP VIEW IF EXISTS v_weekday_completion;
    """,
    """
    CREATE VIEW v_weekday_completion AS
    SELECT 
        t.user_id,
        CAST(strftime('%w', t.due_date) AS INTEGER) as weekday,
        CAST(SUM(CASE WHEN tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(t.id), 0) as completion_rate
    FROM tasks t
    LEFT JOIN task_checkins tc ON t.id = tc.task_id
    WHERE t.due_date IS NOT NULL
    GROUP BY t.user_id, CAST(strftime('%w', t.due_date) AS INTEGER);
    """,
    """
    DROP VIEW IF EXISTS v_calendar_conflicts;
    """,
    """
    CREATE VIEW v_calendar_conflicts AS
    SELECT 
        t.user_id,
        date(t.due_date) as date,
        SUM(CASE WHEN t.external_event_id IS NOT NULL THEN 1 ELSE 0 END) as activities_conflicted,
        CAST(SUM(CASE WHEN t.external_event_id IS NOT NULL AND tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(SUM(CASE WHEN t.external_event_id IS NOT NULL THEN 1 ELSE 0 END), 0) as conflicted_completion_rate,
        CAST(SUM(CASE WHEN t.external_event_id IS NULL AND tc.status IN ('done', 'completed') THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(SUM(CASE WHEN t.external_event_id IS NULL THEN 1 ELSE 0 END), 0) as non_conflicted_completion_rate
    FROM tasks t
    LEFT JOIN task_checkins tc ON t.id = tc.task_id
    WHERE t.due_date IS NOT NULL
    GROUP BY t.user_id, date(t.due_date);
    """,
    """
    DROP VIEW IF EXISTS v_focus_metrics;
    """,
    """
    CREATE VIEW v_focus_metrics AS
    SELECT 
        ms.user_id,
        ms.activity_id,
        CAST(SUM(CASE WHEN se.is_blocked = 0 THEN se.duration_seconds ELSE 0 END) AS FLOAT) / NULLIF(SUM(se.duration_seconds), 0) as focus_ratio,
        SUM(CASE WHEN se.is_blocked = 1 THEN 1 ELSE 0 END) as blocked_attempts
    FROM monitoring_sessions ms
    LEFT JOIN screen_events se ON ms.id = se.session_id
    GROUP BY ms.user_id, ms.activity_id;
    """,
    """
    DROP VIEW IF EXISTS v_recommendation_effect;
    """,
    """
    CREATE VIEW v_recommendation_effect AS
    SELECT 
        ar.user_id,
        ro.recommendation_id,
        ro.decision,
        ar.title,
        date(ro.decided_at) as date
    FROM recommendation_outcomes ro
    JOIN ai_recommendations ar ON ro.recommendation_id = ar.id
    WHERE ro.decision = 'accepted';
    """
]

class AnalyticsViewMigrator:
    """Handles migration and synchronization of database analytics views."""
    
    def __init__(self, connection):
        self.connection = connection
        self.dialect = connection.dialect.name
        
    def drop_views(self):
        """Drops analytics views to allow underlying schema migrations to succeed."""
        if self.dialect == "postgresql":
            views_to_drop = [
                "v_daily_activity_stats",
                "v_daily_subtask_stats",
                "v_missed_reasons_daily",
                "v_time_block_completion",
                "v_weekday_completion",
                "v_calendar_conflicts",
                "v_focus_metrics",
                "v_recommendation_effect"
            ]
            for view in views_to_drop:
                try:
                    with self.connection.begin_nested():
                        self.connection.execute(text(f"DROP VIEW IF EXISTS {view} CASCADE;"))
                except Exception as e:
                    logger.warning(f"Failed to drop view {view}: {e}")
        elif self.dialect == "sqlite":
            # In SQLite, the CREATE VIEW script already contains DROP VIEW IF EXISTS
            pass

    def sync_views(self):
        """Synchronizes the analytics views based on the database dialect."""
        if self.dialect == "postgresql":
            self._execute_statements(POSTGRES_VIEWS, "PG")
        elif self.dialect == "sqlite":
            self._execute_statements(SQLITE_VIEWS, "SQLite")
            
    def _execute_statements(self, statements, dialect_name):
        for stmt in statements:
            try:
                with self.connection.begin_nested():
                    self.connection.execute(text(stmt))
            except Exception as e:
                logger.warning(f"Failed to create {dialect_name} analytics view: {e}")
