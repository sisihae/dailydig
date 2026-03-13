# Plan 06 — Database Repositories (CRUD)

**Phase**: 1 – Project Scaffolding & Infrastructure  
**Creates**: `backend/database/repositories.py`  
**Depends on**: 05 (all SQLAlchemy models)

---

## Goal

Centralized CRUD operations for all models. Every DB interaction goes through these functions.

## Steps

### 1. Create `backend/database/repositories.py`

Organize by model. All functions take an `AsyncSession` parameter.

#### Track CRUD

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Track, DigQueue, TasteProfile, Feedback, RecommendationHistory


async def get_track_by_spotify_id(session: AsyncSession, spotify_id: str) -> Track | None:
    result = await session.execute(select(Track).where(Track.spotify_id == spotify_id))
    return result.scalar_one_or_none()


async def create_track(session: AsyncSession, **kwargs) -> Track:
    track = Track(**kwargs)
    session.add(track)
    await session.flush()
    return track


async def get_track_by_id(session: AsyncSession, track_id: int) -> Track | None:
    return await session.get(Track, track_id)
```

#### DigQueue CRUD

```python
from sqlalchemy import func as sa_func
import random


async def add_to_queue(session: AsyncSession, track_id: int, source: str, playlist_url: str | None = None) -> DigQueue:
    entry = DigQueue(track_id=track_id, source=source, playlist_url=playlist_url)
    session.add(entry)
    await session.flush()
    return entry


async def get_pending_queue(session: AsyncSession) -> list[DigQueue]:
    result = await session.execute(
        select(DigQueue).where(DigQueue.status == "pending").order_by(DigQueue.added_at)
    )
    return list(result.scalars().all())


async def get_pending_count(session: AsyncSession) -> int:
    result = await session.execute(
        select(sa_func.count(DigQueue.id)).where(DigQueue.status == "pending")
    )
    return result.scalar_one()


async def pick_random_pending(session: AsyncSession) -> DigQueue | None:
    pending = await get_pending_queue(session)
    return random.choice(pending) if pending else None


async def mark_delivered(session: AsyncSession, queue_id: int) -> None:
    entry = await session.get(DigQueue, queue_id)
    if entry:
        entry.status = "delivered"
        entry.delivered_at = sa_func.now()


async def is_track_in_queue(session: AsyncSession, track_id: int) -> bool:
    result = await session.execute(
        select(DigQueue.id).where(DigQueue.track_id == track_id).limit(1)
    )
    return result.scalar_one_or_none() is not None
```

#### TasteProfile CRUD

```python
async def get_taste_profile(session: AsyncSession, user_id: int = 1) -> TasteProfile | None:
    result = await session.execute(
        select(TasteProfile).where(TasteProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def upsert_taste_profile(session: AsyncSession, user_id: int = 1, **kwargs) -> TasteProfile:
    profile = await get_taste_profile(session, user_id)
    if profile is None:
        profile = TasteProfile(user_id=user_id, **kwargs)
        session.add(profile)
    else:
        for key, value in kwargs.items():
            setattr(profile, key, value)
    await session.flush()
    return profile
```

#### Feedback CRUD

```python
async def create_feedback(session: AsyncSession, track_id: int, feedback_type: str) -> Feedback:
    fb = Feedback(track_id=track_id, feedback_type=feedback_type)
    session.add(fb)
    await session.flush()
    return fb


async def get_feedback_for_period(session: AsyncSession, days: int = 30) -> list[Feedback]:
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await session.execute(
        select(Feedback).where(Feedback.timestamp >= cutoff)
    )
    return list(result.scalars().all())


async def get_total_feedback_count(session: AsyncSession) -> int:
    result = await session.execute(select(sa_func.count(Feedback.id)))
    return result.scalar_one()
```

#### RecommendationHistory CRUD

```python
async def create_recommendation(session: AsyncSession, **kwargs) -> RecommendationHistory:
    rec = RecommendationHistory(**kwargs)
    session.add(rec)
    await session.flush()
    return rec


async def is_track_recommended(session: AsyncSession, track_id: int) -> bool:
    result = await session.execute(
        select(RecommendationHistory.id)
        .where(RecommendationHistory.track_id == track_id)
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def get_recent_recommendations(session: AsyncSession, days: int = 30) -> list[RecommendationHistory]:
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await session.execute(
        select(RecommendationHistory).where(RecommendationHistory.recommended_at >= cutoff)
    )
    return list(result.scalars().all())


async def get_today_recommendation(session: AsyncSession) -> RecommendationHistory | None:
    from datetime import date
    today = date.today()
    result = await session.execute(
        select(RecommendationHistory)
        .where(sa_func.date(RecommendationHistory.recommended_at) == today)
        .limit(1)
    )
    return result.scalar_one_or_none()
```

## Verification

Write a quick script that creates a track and reads it back via async session.

## Output

- `backend/database/repositories.py` — all CRUD functions for 5 models
