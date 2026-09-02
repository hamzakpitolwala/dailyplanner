import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from backend.core.limiter import limiter

from backend.api.auth_api import router as auth_router
from backend.api.oauth2_api import router as oauth2_router
from backend.api.planner_api import router as planner_router, categories_router
from backend.api.template_api import router as template_router
from backend.api.user_api import router as user_router
from backend.api import fixed_block_api
from backend.core.config import settings
from backend.db.database import Base, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


def sync_alter_tables(connection):
    from sqlalchemy import text
    dialect = connection.dialect.name
    if dialect == "postgresql":
        statements = [
            "ALTER TABLE external_synced_events ADD COLUMN IF NOT EXISTS calendar_id VARCHAR(255);",
            "ALTER TABLE external_synced_events ADD COLUMN IF NOT EXISTS summary VARCHAR(255);",
            "ALTER TABLE external_synced_events ADD COLUMN IF NOT EXISTS description TEXT;",
            "ALTER TABLE external_synced_events ADD COLUMN IF NOT EXISTS location VARCHAR(255);",
            "ALTER TABLE external_synced_events ADD COLUMN IF NOT EXISTS status VARCHAR(50);",
            "ALTER TABLE external_synced_events ADD COLUMN IF NOT EXISTS raw_payload JSONB;",
            "ALTER TABLE external_synced_events ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ;",
            "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'manual';",
            "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS external_event_id UUID;",
            "ALTER TABLE tasks ALTER COLUMN external_event_id TYPE UUID USING external_event_id::uuid;",
            "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) DEFAULT 'normal';",
            "CREATE TABLE IF NOT EXISTS ai_summaries (id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE, period_type VARCHAR(20) NOT NULL, period_start VARCHAR(20) NOT NULL, period_end VARCHAR(20) NOT NULL, summary_text TEXT NOT NULL, wins JSONB NOT NULL DEFAULT '[]', issues JSONB NOT NULL DEFAULT '[]', suggestions JSONB NOT NULL DEFAULT '[]', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());",
            "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS kind VARCHAR(50);",
            "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS scope VARCHAR(50);",
            "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS target_template_id UUID;",
            "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS target_daily_planner_id UUID;",
            "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS target_activity_id UUID;",
            "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS payload JSONB NOT NULL DEFAULT '{}'::jsonb;",
            "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS title VARCHAR(255);",
            "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS explanation TEXT;",
            "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS source_period_start VARCHAR(20);",
            "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS source_period_end VARCHAR(20);",
        ]
        for stmt in statements:
            try:
                with connection.begin_nested():
                    connection.execute(text(stmt))
            except Exception as e:
                logger.warning("PostgreSQL schema migration statement warning: %s", e)
    elif dialect == "sqlite":
        statements = [
            "ALTER TABLE external_synced_events ADD COLUMN calendar_id VARCHAR(255);",
            "ALTER TABLE external_synced_events ADD COLUMN summary VARCHAR(255);",
            "ALTER TABLE external_synced_events ADD COLUMN description TEXT;",
            "ALTER TABLE external_synced_events ADD COLUMN location VARCHAR(255);",
            "ALTER TABLE external_synced_events ADD COLUMN status VARCHAR(50);",
            "ALTER TABLE external_synced_events ADD COLUMN raw_payload JSON;",
            "ALTER TABLE external_synced_events ADD COLUMN last_synced_at DATETIME;",
            "ALTER TABLE tasks ADD COLUMN source VARCHAR(20) DEFAULT 'manual';",
            "ALTER TABLE tasks ADD COLUMN external_event_id VARCHAR(36);",
            "ALTER TABLE tasks ADD COLUMN visibility VARCHAR(20) DEFAULT 'normal';",
            "CREATE TABLE IF NOT EXISTS ai_summaries (id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE, period_type VARCHAR(20) NOT NULL, period_start VARCHAR(20) NOT NULL, period_end VARCHAR(20) NOT NULL, summary_text TEXT NOT NULL, wins JSON NOT NULL DEFAULT '[]', issues JSON NOT NULL DEFAULT '[]', suggestions JSON NOT NULL DEFAULT '[]', created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP);",
            "ALTER TABLE ai_recommendations ADD COLUMN kind VARCHAR(50);",
            "ALTER TABLE ai_recommendations ADD COLUMN scope VARCHAR(50);",
            "ALTER TABLE ai_recommendations ADD COLUMN target_template_id VARCHAR(36);",
            "ALTER TABLE ai_recommendations ADD COLUMN target_daily_planner_id VARCHAR(36);",
            "ALTER TABLE ai_recommendations ADD COLUMN target_activity_id VARCHAR(36);",
            "ALTER TABLE ai_recommendations ADD COLUMN payload JSON NOT NULL DEFAULT '{}';",
            "ALTER TABLE ai_recommendations ADD COLUMN title VARCHAR(255);",
            "ALTER TABLE ai_recommendations ADD COLUMN explanation TEXT;",
            "ALTER TABLE ai_recommendations ADD COLUMN source_period_start VARCHAR(20);",
            "ALTER TABLE ai_recommendations ADD COLUMN source_period_end VARCHAR(20);",
        ]
        for stmt in statements:
            try:
                with connection.begin_nested():
                    connection.execute(text(stmt))
            except Exception:
                pass  # Ignore if column already exists in SQLite


from backend.db.analytics_views import AnalyticsViewMigrator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup - sync our db metadata (models) with db
    async with engine.begin() as conn:
        # Drop analytics views before schema migrations to avoid dependency locks
        await conn.run_sync(lambda connection: AnalyticsViewMigrator(connection).drop_views())
        
        # standard SQLAlchemy models
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(sync_alter_tables)
        # custom analytics views
        await conn.run_sync(lambda connection: AnalyticsViewMigrator(connection).sync_views())
    logger.info("Database tables and schema columns ensured")
    yield


app = FastAPI(title="DailyPlanner API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

cors_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' http: https:;"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

from backend.core.logging import StructuredLoggingMiddleware
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

@app.exception_handler(Exception)
async def standard_exception_handler(request: Request, exc: Exception):
    import traceback
    with open("recent_error.txt", "w") as f:
        traceback.print_exc(file=f)
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."}}
    )

from backend.api.calendar_integration_api import router as calendar_integration_router
from backend.api.ai_api import router as ai_router
from backend.api.ai_recommendations_api import router as ai_recommendations_router
from backend.api.analytics_api import router as analytics_router
from backend.api.agent_api import router as agent_router

app.include_router(auth_router)
app.include_router(oauth2_router)
app.include_router(calendar_integration_router)
app.include_router(fixed_block_api.router)
app.include_router(planner_router)
app.include_router(categories_router)
app.include_router(template_router)
app.include_router(user_router)
app.include_router(ai_router)
app.include_router(ai_recommendations_router)
app.include_router(analytics_router)
app.include_router(agent_router)

# Mount MCP Server
from backend.mcp_server.server import mcp
app.mount("/mcp", mcp.http_app(transport="sse"))


@app.get("/health")
@limiter.limit("10/minute")
def health(request: Request):
    return {"status": "ok"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)

@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
async def chrome_devtools():
    from fastapi.responses import Response
    return Response(status_code=204)
