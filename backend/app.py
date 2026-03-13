from contextlib import asynccontextmanager

from fastapi import FastAPI

import backend.models  # noqa: F401 — register models with Base.metadata
from backend.database.db import init_db
from backend.routes.auth import router as auth_router
from backend.routes.playlist import router as playlist_router
from backend.routes.recommendation import router as recommendation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    # Scheduler will be registered here in Phase 6
    yield
    # Shutdown
    # Scheduler shutdown will be added in Phase 6


app = FastAPI(
    title="DailyDig — Music Discovery Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(playlist_router)
app.include_router(recommendation_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
