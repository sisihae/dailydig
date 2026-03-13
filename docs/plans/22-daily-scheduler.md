# Plan 22 — Daily Scheduler

**Phase**: 6 – LangGraph Orchestration & Scheduler  
**Creates**: `backend/scheduler/__init__.py`, `backend/scheduler/daily_job.py`  
**Depends on**: 21 (LangGraph workflow), 03 (config with schedule settings)

---

## Goal

APScheduler cron job that runs the LangGraph workflow daily at 09:00 KST with Redis-based duplicate protection.

## Steps

### 1. Create `backend/scheduler/__init__.py`

Empty file.

### 2. Create `backend/scheduler/daily_job.py`

```python
import logging
from datetime import date

import redis.asyncio as aioredis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.config import settings
from backend.graph.workflow import build_workflow

logger = logging.getLogger(__name__)

LOCK_KEY_PREFIX = "daily_rec"
LOCK_TTL = 86400  # 24 hours


async def run_daily_recommendation() -> None:
    """
    Daily recommendation job.
    1. Acquire Redis lock to prevent duplicate runs
    2. Run LangGraph workflow (auto-selects queue vs auto-discovery)
    3. Log result
    """
    redis = aioredis.from_url(settings.redis_url)
    lock_key = f"{LOCK_KEY_PREFIX}:{date.today().isoformat()}"

    try:
        # Acquire lock (prevent duplicate runs)
        acquired = await redis.set(lock_key, "1", nx=True, ex=LOCK_TTL)
        if not acquired:
            logger.info("Daily recommendation already ran today. Skipping.")
            return

        logger.info("Starting daily recommendation pipeline...")

        workflow = build_workflow()
        result = await workflow.ainvoke({})

        if result.get("error"):
            logger.error(f"Pipeline error: {result['error']}")
        else:
            logger.info(
                f"Daily recommendation delivered: "
                f"status={result.get('delivery_status')}, "
                f"mode={'queue' if result.get('queue_mode') else 'auto-discovery'}"
            )

    except Exception as e:
        logger.exception(f"Daily recommendation failed: {e}")
        # Release lock so it can retry (manual trigger or next attempt)
        await redis.delete(lock_key)
    finally:
        await redis.aclose()


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_daily_recommendation,
        trigger=CronTrigger(
            hour=settings.schedule_hour,
            minute=settings.schedule_minute,
            timezone=settings.schedule_timezone,
        ),
        id="daily_recommendation",
        replace_existing=True,
    )
    return scheduler
```

### 3. Integrate scheduler into FastAPI lifespan

Update `backend/app.py`:

```python
from backend.scheduler.daily_job import create_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    # Start scheduler
    scheduler = create_scheduler()
    scheduler.start()

    # Start Telegram polling (from Plan 15)
    # telegram_app = create_telegram_app()
    # await telegram_app.initialize()
    # await telegram_app.start()
    # await telegram_app.updater.start_polling(drop_pending_updates=True)

    yield

    # Shutdown
    scheduler.shutdown()
    # await telegram_app.updater.stop()
    # await telegram_app.stop()
    # await telegram_app.shutdown()
```

## Key Decisions

- Redis-based lock key `daily_rec:YYYY-MM-DD` prevents duplicate runs per day.
- Lock released on failure so manual retrigger works.
- Lock TTL = 24h — auto-expires for next day.
- Uses `AsyncIOScheduler` (compatible with FastAPI event loop).
- Schedule configurable via env vars (`SCHEDULE_HOUR`, `SCHEDULE_MINUTE`, `SCHEDULE_TIMEZONE`).

## Verification

1. Set `SCHEDULE_HOUR` / `SCHEDULE_MINUTE` to current time + 1 minute
2. Start app, wait for scheduled run
3. Check logs for "Starting daily recommendation pipeline..."
4. Check Redis for lock key: `GET daily_rec:2026-03-14` → "1"
5. Restart app — second run should log "already ran today"

## Output

- `backend/scheduler/daily_job.py` — cron job + Redis lock
- Updated `backend/app.py` — scheduler integrated in lifespan
