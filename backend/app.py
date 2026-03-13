from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

import backend.models  # noqa: F401 — register models with Base.metadata
from backend.database.db import init_db
from backend.routes.auth import router as auth_router
from backend.routes.feedback import router as feedback_router
from backend.routes.playlist import router as playlist_router
from backend.routes.recommendation import router as recommendation_router
from backend.routes.taste import router as taste_router
from backend.routes.evaluation import router as evaluation_router
from backend.routes.discovery_path import router as discovery_path_router
from backend.scheduler.daily_job import create_scheduler
from backend.services.telegram_handler import create_telegram_app

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()

    # Start Telegram polling for inline button callbacks
    telegram_app = create_telegram_app()
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling(drop_pending_updates=True)
    logger.info("Telegram polling started")

    # Start scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("Scheduler stopped")

    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()
    logger.info("Telegram polling stopped")


app = FastAPI(
    title="DailyDig — Music Discovery Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(playlist_router)
app.include_router(recommendation_router)
app.include_router(feedback_router)
app.include_router(taste_router)
app.include_router(evaluation_router)
app.include_router(discovery_path_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
