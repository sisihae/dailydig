# 5. Data Models

## Track

```python
class Track:
    id: int                  # primary key
    name: str
    artist: str
    album: str | None
    spotify_id: str          # unique

    genre: str | None
    tempo: float | None
    energy: float | None     # 0.0–1.0
    valence: float | None    # 0.0–1.0

    created_at: datetime
```

---

## DigQueue

```python
class DigQueue:
    id: int
    track_id: int            # FK → Track
    user_id: int             # always 1

    source: str              # "playlist_import" | "auto_fetch"
    status: str              # "pending" | "delivered"
    playlist_url: str | None # original playlist URL (for imports)

    added_at: datetime
    delivered_at: datetime | None
```

---

## TasteProfile

```python
class TasteProfile:
    id: int
    user_id: int             # always 1 (single-user)

    genre_preferences: dict  # starts empty {}, built from feedback
    energy_preference: float # starts at 0.5 (neutral)
    era_preference: str | None

    favorite_artists: list[str]   # max 50, built from likes
    recent_likes: list[str]       # max 20, track spotify_ids
    recent_dislikes: list[str]    # max 20, track spotify_ids

    updated_at: datetime
```

Cold start: All preferences start neutral. Genre preferences dict starts empty and is built entirely from feedback.

---

## Feedback

```python
class Feedback:
    id: int
    user_id: int             # always 1
    track_id: int            # FK → Track

    feedback_type: str       # "like" | "dislike" | "skip"

    timestamp: datetime
```

---

## RecommendationHistory

```python
class RecommendationHistory:
    id: int
    user_id: int
    track_id: int            # FK → Track

    source: str              # "queue" | "auto_discovery"
    explanation: str
    score: float | None      # None for queue-sourced tracks
    score_breakdown: dict | None

    recommended_at: datetime
```

    recommended_at: datetime

```

```
