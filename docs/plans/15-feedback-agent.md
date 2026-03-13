# Plan 15 — Telegram Callback Handler & Feedback Agent

**Phase**: 4 – Feedback System  
**Creates**: `backend/agents/feedback_agent.py`, Telegram polling setup  
**Depends on**: 13 (notification service with Telegram bot)

---

## Goal

Handle Telegram inline button presses (👍/👎/⏭), parse callback data, and store feedback.

## Steps

### 1. Create `backend/agents/feedback_agent.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import repositories as repo

VALID_FEEDBACK_TYPES = {"like", "dislike", "skip"}


class FeedbackAgent:
    @staticmethod
    def parse_callback_data(callback_data: str) -> tuple[str, int]:
        """
        Parse Telegram callback data.
        Format: "{feedback_type}:{track_id}"
        Returns: (feedback_type, track_id)
        Raises ValueError on invalid format or feedback type.
        """
        parts = callback_data.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid callback data format: {callback_data}")
        feedback_type = parts[0]
        if feedback_type not in VALID_FEEDBACK_TYPES:
            raise ValueError(f"Invalid feedback type: {feedback_type}")
        track_id = int(parts[1])
        return feedback_type, track_id

    async def process_feedback(
        self, session: AsyncSession, feedback_type: str, track_id: int
    ) -> dict:
        """
        Store feedback in DB.
        Caller is responsible for session commit.
        Returns {"status": "ok", "feedback_type": str, "track_id": int}
        """
        await repo.create_feedback(session, track_id=track_id, feedback_type=feedback_type)
        return {"status": "ok", "feedback_type": feedback_type, "track_id": track_id}
```

### 2. Create Telegram polling handler

File: `backend/services/telegram_handler.py`

```python
import logging

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from backend.config import settings
from backend.agents.feedback_agent import FeedbackAgent
from backend.agents.taste_model_agent import TasteModelAgent
from backend.database.db import async_session

logger = logging.getLogger(__name__)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()  # acknowledge the button press

    try:
        feedback_type, track_id = FeedbackAgent.parse_callback_data(query.data)
    except ValueError:
        logger.warning("Invalid callback data: %s", query.data)
        return

    # Single session for feedback + taste update
    async with async_session() as session:
        feedback_agent = FeedbackAgent()
        await feedback_agent.process_feedback(session, feedback_type, track_id)

        taste_agent = TasteModelAgent()
        await taste_agent.update_from_feedback(session, feedback_type, track_id)

        await session.commit()

    # Confirm to user
    emoji_map = {"like": "👍", "dislike": "👎", "skip": "⏭"}
    emoji = emoji_map.get(feedback_type, "✓")
    await query.edit_message_reply_markup(reply_markup=None)  # remove buttons
    await query.message.reply_text(
        f"{emoji} Feedback recorded! Thanks for helping me learn your taste."
    )


def create_telegram_app() -> Application:
    """Create and configure the Telegram bot application."""
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CallbackQueryHandler(handle_callback))
    return app
```

### 3. Integrate polling into FastAPI lifespan

Update `backend/app.py` lifespan to start/stop Telegram polling:

```python
# In lifespan:
telegram_app = create_telegram_app()
await telegram_app.initialize()
await telegram_app.start()
await telegram_app.updater.start_polling(drop_pending_updates=True)
# ...
# On shutdown:
await telegram_app.updater.stop()
await telegram_app.stop()
await telegram_app.shutdown()
```

### 4. Create backup API endpoint

File: `backend/routes/feedback.py`

```python
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_session
from backend.agents.feedback_agent import FeedbackAgent
from backend.agents.taste_model_agent import TasteModelAgent

router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    track_id: int
    feedback_type: Literal["like", "dislike", "skip"]


@router.post("/feedback")
async def submit_feedback(body: FeedbackRequest, session: AsyncSession = Depends(get_session)):
    """Manual feedback submission (backup for Telegram)."""
    agent = FeedbackAgent()
    result = await agent.process_feedback(session, body.feedback_type, body.track_id)

    taste_agent = TasteModelAgent()
    await taste_agent.update_from_feedback(session, body.feedback_type, body.track_id)

    await session.commit()
    return result
```

## Key Decisions

- Telegram polling mode (no webhook, no public URL needed).
- Callback data parsed from `{type}:{track_id}` format set in delivery.
- Buttons removed after feedback to prevent double-submit.
- Backup `/feedback` POST endpoint for non-Telegram testing.
- Feedback → taste update runs inline (fast enough for single user).

## Verification

1. Trigger a recommendation (sends Telegram message with buttons)
2. Press 👍 in Telegram
3. Check DB: new row in `feedback` table
4. Bot replies with confirmation

## Output

- `backend/agents/feedback_agent.py` — callback parsing + feedback storage
- `backend/services/telegram_handler.py` — Telegram polling + callback handler
- `backend/routes/feedback.py` — backup API endpoint
