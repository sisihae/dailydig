import logging
from datetime import date

import redis.asyncio as aioredis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.config import settings
from backend.database.db import async_session
from backend.evaluation.metrics import MetricsCalculator
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

        # Save daily metrics snapshot
        try:
            async with async_session() as session:
                calculator = MetricsCalculator()
                await calculator.save_daily_snapshot(session)
                await session.commit()
            logger.info("Daily metrics snapshot saved")
        except Exception:
            logger.exception("Failed to save daily metrics snapshot")

    except Exception:
        logger.exception("Daily recommendation failed")
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
