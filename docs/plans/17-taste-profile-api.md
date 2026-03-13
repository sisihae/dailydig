# Plan 17 — Taste Profile API Endpoint

**Phase**: 4 – Feedback System  
**Creates**: `backend/routes/taste.py`  
**Depends on**: 16 (taste model agent), 06 (repositories)

---

## Goal

Expose `GET /taste-profile` for viewing the learned taste profile.

## Steps

### 1. Create `backend/routes/taste.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_session
from backend.database import repositories as repo

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
```

### 2. Register router in `backend/app.py`

```python
from backend.routes.taste import router as taste_router
from backend.routes.feedback import router as feedback_router
app.include_router(taste_router)
app.include_router(feedback_router)
```

## Verification

```bash
curl http://localhost:8000/taste-profile
# → 404 (no feedback yet) or taste profile JSON
```

## Output

- `backend/routes/taste.py` — `/taste-profile` endpoint
- Updated `backend/app.py` — routers registered
