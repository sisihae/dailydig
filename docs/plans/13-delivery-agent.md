# Plan 13 — Delivery Agent (Telegram)

**Phase**: 3 – Queue Delivery + Analysis Agent  
**Creates**: `backend/agents/delivery_agent.py`, `backend/services/notification_service.py`  
**Depends on**: 03 (config with Telegram tokens)

---

## Goal

Send daily track recommendation to user via Telegram with inline feedback buttons.

## Steps

### 1. Create `backend/services/notification_service.py`

Low-level Telegram API wrapper.

```python
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from backend.config import settings


class NotificationService:
    def __init__(self):
        self.bot = Bot(token=settings.telegram_bot_token)
        self.chat_id = settings.telegram_chat_id

    async def send_track_message(
        self,
        artist: str,
        track_name: str,
        album: str | None,
        explanation: str,
        spotify_url: str,
        track_id: int,
    ) -> int:
        """
        Send formatted track message with inline feedback buttons.
        Returns the Telegram message_id.
        """
        text = (
            f"🎵 *Today's Music Discovery*\n\n"
            f"*Artist:* {self._escape_md(artist)}\n"
            f"*Track:* {self._escape_md(track_name)}\n"
            f"*Album:* {self._escape_md(album or 'Unknown')}\n\n"
            f"_About this track:_\n"
            f"{self._escape_md(explanation)}\n\n"
            f"🔗 [Listen on Spotify]({spotify_url})"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👍 Like", callback_data=f"like:{track_id}"),
                InlineKeyboardButton("👎 Dislike", callback_data=f"dislike:{track_id}"),
                InlineKeyboardButton("⏭ Skip", callback_data=f"skip:{track_id}"),
            ]
        ])

        message = await self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
        return message.message_id

    async def send_notification(self, text: str) -> int:
        """Send a plain text notification."""
        message = await self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
        )
        return message.message_id

    @staticmethod
    def _escape_md(text: str) -> str:
        """Escape Markdown special characters for Telegram."""
        for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            text = text.replace(char, f'\\{char}')
        return text
```

### 2. Create `backend/agents/delivery_agent.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import repositories as repo
from backend.services.notification_service import NotificationService


class DeliveryAgent:
    def __init__(self):
        self.notification = NotificationService()

    async def deliver_track(
        self,
        session: AsyncSession,
        track_id: int,
        queue_entry_id: int | None,
        explanation: str,
        source: str,
        score: float | None = None,
        score_breakdown: dict | None = None,
    ) -> dict:
        """
        Deliver a track to the user:
        1. Send Telegram message with explanation + feedback buttons
        2. Mark queue entry as delivered (if from queue)
        3. Store in recommendation_history

        Returns {"message_id": int, "delivery_status": str}
        """
        track = await repo.get_track_by_id(session, track_id)
        if not track:
            return {"message_id": None, "delivery_status": "error_track_not_found"}

        spotify_url = f"https://open.spotify.com/track/{track.spotify_id}"

        try:
            message_id = await self.notification.send_track_message(
                artist=track.artist,
                track_name=track.name,
                album=track.album,
                explanation=explanation,
                spotify_url=spotify_url,
                track_id=track.id,
            )
            delivery_status = "delivered"
        except Exception:
            message_id = None
            delivery_status = "undelivered"

        # Mark queue entry as delivered
        if queue_entry_id:
            await repo.mark_delivered(session, queue_entry_id)

        # Store in recommendation history
        await repo.create_recommendation(
            session,
            track_id=track.id,
            source=source,
            explanation=explanation,
            score=score,
            score_breakdown=score_breakdown,
        )

        await session.commit()

        return {"message_id": message_id, "delivery_status": delivery_status}

    async def send_auto_discovery_notice(self) -> None:
        """Notify user that queue is empty and switching to auto-discovery."""
        await self.notification.send_notification(
            "🔄 Your dig queue is empty. Switching to auto-discovery based on your feedback!"
        )
```

## Key Decisions

- Telegram message uses MarkdownV2 formatting with escaped special chars.
- Callback data format: `{feedback_type}:{track_id}` — parsed by Feedback Agent.
- If Telegram send fails, recommendation still stored as "undelivered" (retrievable via API).
- Auto-discovery notice is a separate plain-text message.

## Verification

```python
agent = DeliveryAgent()
result = await agent.deliver_track(session, track_id=1, queue_entry_id=1,
    explanation="Great neo-soul track...", source="queue")
print(result)  # {"message_id": 123, "delivery_status": "delivered"}
```

## Output

- `backend/services/notification_service.py` — Telegram bot wrapper
- `backend/agents/delivery_agent.py` — delivery orchestration
