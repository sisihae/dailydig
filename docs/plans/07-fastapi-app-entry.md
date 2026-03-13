# Plan 07 — FastAPI App Entry Point

**Phase**: 1 – Project Scaffolding & Infrastructure  
**Creates**: `backend/app.py`  
**Depends on**: 04 (db init), 03 (config)

---

## Goal

Create the FastAPI application with lifespan handler for DB init and scheduler startup.

## Steps

### 1. Create `backend/app.py`

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
```

### 2. Router registration (placeholder)

Routes will be added incrementally in later phases. The structure will be:

```python
# Added in Phase 2:
# from backend.routes.playlist import router as playlist_router
# app.include_router(playlist_router)

# Added in Phase 3:
# from backend.routes.recommendation import router as recommendation_router
# app.include_router(recommendation_router)
```

Routers will live in `backend/routes/` (create directory as needed).

## Verification

```bash
poetry run uvicorn backend.app:app --reload
# Visit http://localhost:8000/health → {"status": "ok"}
# Visit http://localhost:8000/docs → Swagger UI loads
```

## Output

- `backend/app.py` — FastAPI app with lifespan, health endpoint
