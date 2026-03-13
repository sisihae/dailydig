from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_session
from backend.database import repositories as repo
from backend.models import RecommendationHistory

router = APIRouter(tags=["discovery"])


@router.get("/discovery-path/{track_id}")
async def get_discovery_path(
    track_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Get track metadata + score breakdown for a recommended track.
    Shows how and why this track was recommended.
    """
    track = await repo.get_track_by_id(session, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found.")

    # Find recommendation entry for this track
    result = await session.execute(
        select(RecommendationHistory)
        .where(RecommendationHistory.track_id == track_id)
        .order_by(RecommendationHistory.recommended_at.desc())
        .limit(1)
    )
    rec = result.scalar_one_or_none()

    return {
        "track": {
            "id": track.id,
            "name": track.name,
            "artist": track.artist,
            "album": track.album,
            "spotify_id": track.spotify_id,
            "genre": track.genre,
            "energy": track.energy,
            "valence": track.valence,
            "tempo": track.tempo,
        },
        "recommendation": {
            "source": rec.source,
            "explanation": rec.explanation,
            "score": rec.score,
            "score_breakdown": rec.score_breakdown,
            "recommended_at": rec.recommended_at.isoformat(),
        } if rec else None,
    }
