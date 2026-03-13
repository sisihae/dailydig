# Plan 14 — Trigger Recommendation Endpoint

**Phase**: 3 – Queue Delivery + Analysis Agent  
**Creates**: `backend/routes/recommendation.py`  
**Depends on**: 12 (analysis agent), 13 (delivery agent), 10 (queue service)

---

## Goal

Expose `/trigger-recommendation` and `/recommendation/today` endpoints for manual testing of the queue delivery pipeline.

## Steps

### 1. Create `backend/routes/recommendation.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_session
from backend.database import repositories as repo
from backend.services.spotify_service import SpotifyService
from backend.services.queue_service import QueueService
from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.delivery_agent import DeliveryAgent

router = APIRouter(tags=["recommendation"])


@router.post("/trigger-recommendation")
async def trigger_recommendation(session: AsyncSession = Depends(get_session)):
    """
    Manually trigger the daily recommendation pipeline.
    For development/testing — in production, the scheduler handles this.
    """
    queue_service = QueueService(SpotifyService())

    # Check queue
    queue_entry, track = await queue_service.pick_random_track(session)

    if queue_entry is None:
        # Queue is empty — return info (auto-discovery handled in Phase 5)
        raise HTTPException(
            status_code=404,
            detail="Queue is empty. Import a playlist first, or wait for auto-discovery (Phase 5).",
        )

    # Generate explanation
    analysis_agent = AnalysisAgent()
    explanation = await analysis_agent.generate_explanation(
        track={
            "artist": track.artist,
            "track_name": track.name,
            "genre": track.genre,
            "energy": track.energy,
            "valence": track.valence,
            "tempo": track.tempo,
            "album": track.album,
        },
        queue_mode=True,
    )

    # Deliver
    delivery_agent = DeliveryAgent()
    result = await delivery_agent.deliver_track(
        session=session,
        track_id=track.id,
        queue_entry_id=queue_entry.id,
        explanation=explanation,
        source="queue",
    )

    return {
        "track": {"name": track.name, "artist": track.artist, "album": track.album},
        "explanation": explanation,
        "delivery": result,
    }


@router.get("/recommendation/today")
async def get_today_recommendation(session: AsyncSession = Depends(get_session)):
    """Get today's recommendation if it exists."""
    rec = await repo.get_today_recommendation(session)
    if rec is None:
        raise HTTPException(status_code=404, detail="No recommendation today yet.")

    track = await repo.get_track_by_id(session, rec.track_id)
    return {
        "track": {
            "name": track.name,
            "artist": track.artist,
            "album": track.album,
            "spotify_id": track.spotify_id,
        },
        "explanation": rec.explanation,
        "source": rec.source,
        "score": rec.score,
        "score_breakdown": rec.score_breakdown,
        "recommended_at": rec.recommended_at.isoformat(),
    }
```

### 2. Register router in `backend/app.py`

```python
from backend.routes.recommendation import router as recommendation_router
app.include_router(recommendation_router)
```

## Verification

```bash
# After importing a playlist:
curl -X POST http://localhost:8000/trigger-recommendation
# → Returns track info + explanation, sends Telegram message

curl http://localhost:8000/recommendation/today
# → Returns today's recommendation
```

## Output

- `backend/routes/recommendation.py` — `/trigger-recommendation`, `/recommendation/today`
- Updated `backend/app.py` — router registered
