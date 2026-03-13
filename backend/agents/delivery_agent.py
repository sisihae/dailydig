from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import repositories as repo
from backend.services.notification_service import NotificationService


class DeliveryAgent:
    def __init__(self) -> None:
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

        Returns {"message_id": int | None, "delivery_status": str}
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
