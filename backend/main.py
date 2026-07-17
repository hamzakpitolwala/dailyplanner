import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth_api import router as auth_router
from backend.api.history_api import router as history_router
from backend.api.oauth2_api import router as oauth2_router
from backend.api.planner_api import router as planner_router
from backend.api.template_api import router as template_router
from backend.core.config import settings
from backend.db.database import Base, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")
    yield


app = FastAPI(title="DailyPlanner API", lifespan=lifespan)

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

app.include_router(auth_router)
app.include_router(oauth2_router)
app.include_router(planner_router)
app.include_router(history_router)
app.include_router(template_router)


@app.get("/health")
def health():
    return {"status": "ok"}
