from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import repositories as repo
from backend.database.db import get_session

router = APIRouter(tags=["taste"])


@router.get("/taste-profile")
async def get_taste_profile(session: AsyncSession = Depends(get_session)):
    """View the current feedback-learned taste profile."""
    profile = await repo.get_taste_profile(session)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="No taste profile yet. Provide feedback on some tracks first.",
        )

    return {
        "genre_preferences": profile.genre_preferences,
        "energy_preference": profile.energy_preference,
        "era_preference": profile.era_preference,
        "favorite_artists": profile.favorite_artists,
        "recent_likes": profile.recent_likes,
        "recent_dislikes": profile.recent_dislikes,
        "updated_at": profile.updated_at.isoformat(),
    }
