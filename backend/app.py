from contextlib import asynccontextmanager

from fastapi import FastAPI

import backend.models  # noqa: F401 — register models with Base.metadata
from backend.database.db import init_db


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


@app.get("/health")
async def health_check():
    return {"status": "ok"}
