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
            if genre:
                genre_prefs[genre] = genre_prefs.get(genre, GENRE_DEFAULT) + LIKE_GENRE_DELTA

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
            if genre:
                genre_prefs[genre] = genre_prefs.get(genre, GENRE_DEFAULT) + DISLIKE_GENRE_DELTA

            # Add to recent dislikes (cap at 20, FIFO)
            recent_dislikes.append(track.spotify_id)
            if len(recent_dislikes) > MAX_RECENT_TRACKS:
                recent_dislikes = recent_dislikes[-MAX_RECENT_TRACKS:]

        elif feedback_type == "skip":
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
