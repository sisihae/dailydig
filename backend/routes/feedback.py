from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.feedback_agent import FeedbackAgent
from backend.agents.taste_model_agent import TasteModelAgent
from backend.database.db import get_session

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
