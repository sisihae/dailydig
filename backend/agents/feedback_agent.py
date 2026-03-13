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
