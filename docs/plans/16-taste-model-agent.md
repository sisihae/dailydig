# Plan 16 — Taste Modeling Agent

**Phase**: 4 – Feedback System  
**Creates**: `backend/agents/taste_model_agent.py`  
**Depends on**: 06 (repositories), 05 (TasteProfile model)

---

## Goal

Update user taste profile based on feedback with specific learning rates. Handles cold start (empty profile creation).

## Steps

### 1. Create `backend/agents/taste_model_agent.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import repositories as repo


# Learning rates
LIKE_GENRE_DELTA = 0.05
DISLIKE_GENRE_DELTA = -0.05
SKIP_GENRE_DELTA = -0.02
ENERGY_DELTA = 0.02
GENRE_DEFAULT = 0.5
MAX_FAVORITE_ARTISTS = 50
MAX_RECENT_TRACKS = 20


class TasteModelAgent:
    async def update_from_feedback(
        self, session: AsyncSession, feedback_type: str, track_id: int
    ) -> None:
        """
        Update taste profile based on feedback.
        Caller is responsible for session commit.

        Learning rates:
        - like:    genre += 0.05, energy moves 0.02 toward track's energy, add artist
        - dislike: genre -= 0.05, add to recent_dislikes
        - skip:    genre -= 0.02 (weaker negative signal)

        Cold start: creates empty TasteProfile if none exists.
        """
        track = await repo.get_track_by_id(session, track_id)
        if not track:
            return

        profile = await repo.get_taste_profile(session)

        # Cold start: create empty profile
        if profile is None:
            profile = await repo.upsert_taste_profile(
                session,
                genre_preferences={},
                energy_preference=0.5,
                favorite_artists=[],
                recent_likes=[],
                recent_dislikes=[],
            )

        genre_prefs = dict(profile.genre_preferences)
        energy_pref = profile.energy_preference
        fav_artists = list(profile.favorite_artists)
        recent_likes = list(profile.recent_likes)
        recent_dislikes = list(profile.recent_dislikes)

        genre = track.genre

        if feedback_type == "like":
            # Genre: increase preference
            if genre:
                genre_prefs[genre] = genre_prefs.get(genre, GENRE_DEFAULT) + LIKE_GENRE_DELTA

            # Energy: move toward track's energy
            if track.energy is not None:
                energy_pref += ENERGY_DELTA * (track.energy - energy_pref)

            # Add artist to favorites (cap at 50, FIFO)
            if track.artist not in fav_artists:
                fav_artists.append(track.artist)
                if len(fav_artists) > MAX_FAVORITE_ARTISTS:
                    fav_artists = fav_artists[-MAX_FAVORITE_ARTISTS:]

            # Add to recent likes (cap at 20, FIFO)
            recent_likes.append(track.spotify_id)
            if len(recent_likes) > MAX_RECENT_TRACKS:
                recent_likes = recent_likes[-MAX_RECENT_TRACKS:]

        elif feedback_type == "dislike":
            # Genre: decrease preference
            if genre:
                genre_prefs[genre] = genre_prefs.get(genre, GENRE_DEFAULT) + DISLIKE_GENRE_DELTA

            # Add to recent dislikes (cap at 20, FIFO)
            recent_dislikes.append(track.spotify_id)
            if len(recent_dislikes) > MAX_RECENT_TRACKS:
                recent_dislikes = recent_dislikes[-MAX_RECENT_TRACKS:]

        elif feedback_type == "skip":
            # Genre: weaker negative signal
            if genre:
                genre_prefs[genre] = genre_prefs.get(genre, GENRE_DEFAULT) + SKIP_GENRE_DELTA

        # Clamp all genre preferences to [0.0, 1.0]
        genre_prefs = {k: max(0.0, min(1.0, v)) for k, v in genre_prefs.items()}

        # Save updated profile
        await repo.upsert_taste_profile(
            session,
            genre_preferences=genre_prefs,
            energy_preference=energy_pref,
            favorite_artists=fav_artists,
            recent_likes=recent_likes,
            recent_dislikes=recent_dislikes,
        )
```

## Key Logic Summary

| Feedback | Genre Pref | Energy             | Artists      | Likes/Dislikes           |
| -------- | ---------- | ------------------ | ------------ | ------------------------ |
| like     | +0.05      | +0.02 toward track | Add (cap 50) | Add to likes (cap 20)    |
| dislike  | -0.05      | —                  | —            | Add to dislikes (cap 20) |
| skip     | -0.02      | —                  | —            | —                        |

- New genres start at 0.5 (neutral)
- All values clamped to [0.0, 1.0]
- FIFO eviction on capped lists

## Verification

1. Start with no TasteProfile in DB
2. Submit "like" feedback for a track with genre "neo soul"
3. Check: `TasteProfile.genre_preferences` = `{"neo soul": 0.55}`
4. Submit "dislike" for a "jazz" track
5. Check: `genre_preferences` = `{"neo soul": 0.55, "jazz": 0.45}`

## Output

- `backend/agents/taste_model_agent.py` — feedback-driven taste profile learning
