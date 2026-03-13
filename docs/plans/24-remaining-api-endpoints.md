# Plan 24 — Remaining API Endpoints

**Phase**: 7 – Evaluation System & Remaining API Endpoints  
**Creates**: `backend/routes/evaluation.py`, `backend/routes/discovery_path.py`  
**Depends on**: 23 (metrics), 06 (repositories)

---

## Goal

Implement the remaining 2 API endpoints: `/evaluation/metrics` and `/discovery-path/{track_id}`.

## Steps

### 1. Create `backend/routes/evaluation.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_session
from backend.evaluation.metrics import MetricsCalculator

router = APIRouter(tags=["evaluation"])


@router.get("/evaluation/metrics")
async def get_metrics(
    days: int = 30,
    session: AsyncSession = Depends(get_session),
):
    """
    Get evaluation metrics for the specified period.

    Query params:
    - days: rolling window size (default 30)
    """
    calculator = MetricsCalculator()
    return await calculator.calculate_metrics(session, days=days)
```

### 2. Create `backend/routes/discovery_path.py`

```python
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
            "source": rec.source if rec else None,
            "explanation": rec.explanation if rec else None,
            "score": rec.score if rec else None,
            "score_breakdown": rec.score_breakdown if rec else None,
            "recommended_at": rec.recommended_at.isoformat() if rec else None,
        } if rec else None,
    }
```

### 3. Register routers in `backend/app.py`

```python
from backend.routes.evaluation import router as evaluation_router
from backend.routes.discovery_path import router as discovery_path_router
app.include_router(evaluation_router)
app.include_router(discovery_path_router)
```

## Complete API Endpoint Summary

| #   | Method | Path                         | Plan          |
| --- | ------ | ---------------------------- | ------------- |
| 1   | `POST` | `/import-playlist`           | Plan 11       |
| 2   | `GET`  | `/queue`                     | Plan 11       |
| 3   | `GET`  | `/recommendation/today`      | Plan 14       |
| 4   | `POST` | `/feedback`                  | Plan 15       |
| 5   | `GET`  | `/taste-profile`             | Plan 17       |
| 6   | `GET`  | `/discovery-path/{track_id}` | **This plan** |
| 7   | `POST` | `/trigger-recommendation`    | Plan 14       |
| 8   | `GET`  | `/evaluation/metrics`        | **This plan** |
| 9   | `GET`  | `/auth/spotify`              | Plan 08       |
| 10  | `GET`  | `/auth/callback`             | Plan 08       |
| 11  | `GET`  | `/health`                    | Plan 07       |

## Verification

```bash
curl http://localhost:8000/evaluation/metrics?days=30
curl http://localhost:8000/discovery-path/1
```

## Output

- `backend/routes/evaluation.py` — `/evaluation/metrics`
- `backend/routes/discovery_path.py` — `/discovery-path/{track_id}`
- Updated `backend/app.py` — routers registered
