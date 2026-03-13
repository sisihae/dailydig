# Plan 05 — SQLAlchemy Models

**Phase**: 1 – Project Scaffolding & Infrastructure  
**Creates**: `backend/models/*.py` (5 model files)  
**Depends on**: 04 (Base from db.py)

---

## Goal

Define all 5 SQLAlchemy ORM models matching the data-models spec.

## Steps

### 1. Create `backend/models/__init__.py`

```python
from backend.models.track import Track
from backend.models.dig_queue import DigQueue
from backend.models.taste_profile import TasteProfile
from backend.models.feedback import Feedback
from backend.models.recommendation_history import RecommendationHistory

__all__ = ["Track", "DigQueue", "TasteProfile", "Feedback", "RecommendationHistory"]
```

### 2. Create `backend/models/track.py`

```python
from datetime import datetime

from sqlalchemy import String, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    artist: Mapped[str] = mapped_column(String(500))
    album: Mapped[str | None] = mapped_column(String(500), nullable=True)
    spotify_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    genre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tempo: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy: Mapped[float | None] = mapped_column(Float, nullable=True)
    valence: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### 3. Create `backend/models/dig_queue.py`

```python
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class DigQueue(Base):
    __tablename__ = "dig_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"))
    user_id: Mapped[int] = mapped_column(Integer, default=1)

    source: Mapped[str] = mapped_column(String(50))  # "playlist_import" | "auto_fetch"
    status: Mapped[str] = mapped_column(String(20), default="pending")  # "pending" | "delivered"
    playlist_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

### 4. Create `backend/models/taste_profile.py`

```python
from datetime import datetime

from sqlalchemy import Integer, Float, String, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class TasteProfile(Base):
    __tablename__ = "taste_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, default=1)

    genre_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    energy_preference: Mapped[float] = mapped_column(Float, default=0.5)
    era_preference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    favorite_artists: Mapped[list] = mapped_column(JSON, default=list)
    recent_likes: Mapped[list] = mapped_column(JSON, default=list)
    recent_dislikes: Mapped[list] = mapped_column(JSON, default=list)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
```

### 5. Create `backend/models/feedback.py`

```python
from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1)
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"))

    feedback_type: Mapped[str] = mapped_column(String(20))  # "like" | "dislike" | "skip"

    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### 6. Create `backend/models/recommendation_history.py`

```python
from datetime import datetime

from sqlalchemy import Integer, Float, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1)
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"))

    source: Mapped[str] = mapped_column(String(50))  # "queue" | "auto_discovery"
    explanation: Mapped[str] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    recommended_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

## Verification

```python
from backend.database.db import init_db
import asyncio
asyncio.run(init_db())
# Check PostgreSQL: \dt should show 5 tables
```

## Output

- 5 model files in `backend/models/`
- `__init__.py` re-exporting all models
