# Plan 23 — Evaluation Metrics System

**Phase**: 7 – Evaluation System & Remaining API Endpoints  
**Creates**: `backend/evaluation/__init__.py`, `backend/evaluation/metrics.py`  
**Depends on**: 06 (repositories), 05 (Feedback, RecommendationHistory models)

---

## Goal

Calculate rolling 30-day engagement and discovery quality metrics, with daily snapshot storage.

## Steps

### 1. Create `backend/evaluation/__init__.py`

Empty file.

### 2. Create evaluation_metrics model

Add to `backend/models/evaluation_metrics.py`:

```python
from datetime import date

from sqlalchemy import Integer, Float, Date, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class EvaluationMetrics(Base):
    __tablename__ = "evaluation_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, unique=True)

    # Engagement
    total_recommendations: Mapped[int] = mapped_column(Integer, default=0)
    like_rate: Mapped[float] = mapped_column(Float, default=0.0)
    dislike_rate: Mapped[float] = mapped_column(Float, default=0.0)
    skip_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Discovery quality
    new_artist_rate: Mapped[float] = mapped_column(Float, default=0.0)
    genre_diversity: Mapped[float] = mapped_column(Float, default=0.0)
```

Update `backend/models/__init__.py` to include it.

### 3. Create `backend/evaluation/metrics.py`

```python
from datetime import date, datetime, timedelta

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Feedback, RecommendationHistory, Track
from backend.models.evaluation_metrics import EvaluationMetrics


class MetricsCalculator:
    async def calculate_metrics(self, session: AsyncSession, days: int = 30) -> dict:
        """
        Calculate rolling metrics for the last N days.

        Engagement:
        - like_rate = likes / total_recommendations
        - dislike_rate = dislikes / total_recommendations
        - skip_rate = skips / total_recommendations

        Discovery Quality:
        - new_artist_rate = first_time_artists / total_recommendations
        - genre_diversity = unique_genres / total_recommendations
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Total recommendations in period
        rec_result = await session.execute(
            select(sa_func.count(RecommendationHistory.id))
            .where(RecommendationHistory.recommended_at >= cutoff)
        )
        total_recs = rec_result.scalar_one()

        if total_recs == 0:
            return {
                "total_recommendations": 0,
                "like_rate": 0.0,
                "dislike_rate": 0.0,
                "skip_rate": 0.0,
                "new_artist_rate": 0.0,
                "genre_diversity": 0.0,
                "period_days": days,
            }

        # Feedback counts
        feedback_result = await session.execute(
            select(Feedback.feedback_type, sa_func.count(Feedback.id))
            .where(Feedback.timestamp >= cutoff)
            .group_by(Feedback.feedback_type)
        )
        feedback_counts = dict(feedback_result.all())
        likes = feedback_counts.get("like", 0)
        dislikes = feedback_counts.get("dislike", 0)
        skips = feedback_counts.get("skip", 0)

        # New artist rate: artists recommended for the first time in this period
        recs_in_period = await session.execute(
            select(RecommendationHistory)
            .where(RecommendationHistory.recommended_at >= cutoff)
        )
        recs = list(recs_in_period.scalars().all())

        new_artists = 0
        unique_genres = set()

        for rec in recs:
            track = await session.get(Track, rec.track_id)
            if not track:
                continue

            if track.genre:
                unique_genres.add(track.genre)

            # Check if this artist was ever recommended before this period
            prior = await session.execute(
                select(sa_func.count(RecommendationHistory.id))
                .join(Track, RecommendationHistory.track_id == Track.id)
                .where(Track.artist == track.artist)
                .where(RecommendationHistory.recommended_at < cutoff)
            )
            if prior.scalar_one() == 0:
                new_artists += 1

        return {
            "total_recommendations": total_recs,
            "like_rate": round(likes / total_recs, 3),
            "dislike_rate": round(dislikes / total_recs, 3),
            "skip_rate": round(skips / total_recs, 3),
            "new_artist_rate": round(new_artists / total_recs, 3),
            "genre_diversity": round(len(unique_genres) / total_recs, 3),
            "period_days": days,
        }

    async def save_daily_snapshot(self, session: AsyncSession) -> None:
        """Save today's metrics as a daily snapshot."""
        metrics = await self.calculate_metrics(session)
        today = date.today()

        existing = await session.execute(
            select(EvaluationMetrics).where(EvaluationMetrics.snapshot_date == today)
        )
        snapshot = existing.scalar_one_or_none()

        if snapshot:
            for key, value in metrics.items():
                if key != "period_days" and hasattr(snapshot, key):
                    setattr(snapshot, key, value)
        else:
            snapshot = EvaluationMetrics(
                snapshot_date=today,
                total_recommendations=metrics["total_recommendations"],
                like_rate=metrics["like_rate"],
                dislike_rate=metrics["dislike_rate"],
                skip_rate=metrics["skip_rate"],
                new_artist_rate=metrics["new_artist_rate"],
                genre_diversity=metrics["genre_diversity"],
            )
            session.add(snapshot)

        await session.flush()
```

## Verification

```python
calc = MetricsCalculator()
metrics = await calc.calculate_metrics(session, days=30)
print(metrics)
# {"total_recommendations": 15, "like_rate": 0.6, ...}
```

## Output

- `backend/models/evaluation_metrics.py` — EvaluationMetrics model
- `backend/evaluation/metrics.py` — MetricsCalculator with snapshot storage
