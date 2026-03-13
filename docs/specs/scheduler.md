# 9. Scheduler

Daily recommendation job using APScheduler (`AsyncIOScheduler`).

Schedule: Every day at 09:00 KST (configurable via env vars).

```python
scheduler.add_job(
    run_daily_recommendation,
    trigger=CronTrigger(hour=9, minute=0, timezone="Asia/Seoul"),
    id="daily_recommendation",
    replace_existing=True
)
```

## Job Logic

1. Check dig queue for pending tracks
2. If queue has tracks → **Queue Mode**: pick random, analyze, deliver
3. If queue is empty → **Auto-Discovery Mode**:
   a. Send Telegram notification ("Queue empty — switching to auto-discovery")
   b. Load TasteProfile (feedback-learned)
   c. Run Planner → Discovery → Ranking pipeline
   d. Best track delivered, remaining candidates added to queue
4. Log result (success/error)
5. Redis-based lock key (`daily_rec:{date}`) to prevent duplicate runs

Registered in FastAPI lifespan (start on app startup, shutdown on app shutdown).
