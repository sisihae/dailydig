import random

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import repositories as repo


# Default strategy weights
DEFAULT_TASTE_WEIGHT = 0.5
DEFAULT_NOVELTY_WEIGHT = 0.3
DEFAULT_DIVERSITY_WEIGHT = 0.2
HIGH_EXPLORATION_NOVELTY = 0.4
HIGH_EXPLORATION_TASTE = 0.3
HIGH_EXPLORATION_DIVERSITY = 0.3
DISLIKE_RATE_THRESHOLD = 0.4
SPARSE_FEEDBACK_THRESHOLD = 5


class PlannerAgent:
    async def create_strategy(self, session: AsyncSession) -> dict:
        """
        Build a discovery strategy from the taste profile and recent history.

        Logic:
        - If dislike_rate > 40%: increase exploration (explore new genres)
        - Pick top 2-3 genres from genre_preferences as candidate_genres
        - Pick top 2-3 artists from favorite_artists as seed_artists
        - If sparse profile (< 5 feedback): fallback to recently delivered tracks
        - Respect Spotify's 5-seed limit (artists + genres combined)

        Returns: PlannerStrategy dict
        """
        profile = await repo.get_taste_profile(session)
        feedback_count = await repo.get_total_feedback_count(session)
        recent_recs = await repo.get_recent_recommendations(session, days=30)

        # Calculate recent dislike rate
        recent_feedback = await repo.get_feedback_for_period(session, days=30)
        if recent_feedback:
            dislikes = sum(1 for f in recent_feedback if f.feedback_type == "dislike")
            dislike_rate = dislikes / len(recent_feedback)
        else:
            dislike_rate = 0.0

        # Determine exploration ratio
        high_exploration = dislike_rate > DISLIKE_RATE_THRESHOLD

        if high_exploration:
            exploration_ratio = 0.5
            taste_weight = HIGH_EXPLORATION_TASTE
            novelty_weight = HIGH_EXPLORATION_NOVELTY
            diversity_weight = HIGH_EXPLORATION_DIVERSITY
        else:
            exploration_ratio = 0.3
            taste_weight = DEFAULT_TASTE_WEIGHT
            novelty_weight = DEFAULT_NOVELTY_WEIGHT
            diversity_weight = DEFAULT_DIVERSITY_WEIGHT

        # Build candidate genres and seed artists
        candidate_genres: list[str] = []
        seed_artists: list[str] = []

        if profile and feedback_count >= SPARSE_FEEDBACK_THRESHOLD:
            # Sufficient feedback — use learned preferences
            genre_prefs = profile.genre_preferences or {}
            if genre_prefs:
                # Weighted random sample of top genres
                sorted_genres = sorted(genre_prefs.items(), key=lambda x: x[1], reverse=True)
                top_genres = [g for g, _ in sorted_genres[:8]]
                weights = [w for _, w in sorted_genres[:8]]
                sample_size = min(3, len(top_genres))
                candidate_genres = random.choices(top_genres, weights=weights, k=sample_size)
                candidate_genres = list(set(candidate_genres))  # dedup

            fav_artists = profile.favorite_artists or []
            if fav_artists:
                sample_size = min(2, len(fav_artists))
                seed_artists = random.sample(fav_artists, sample_size)

        else:
            # Sparse profile — fallback to genres from recent recommendations
            if recent_recs:
                for rec in recent_recs[:10]:
                    track = await repo.get_track_by_id(session, rec.track_id)
                    if track and track.genre and track.genre not in candidate_genres:
                        candidate_genres.append(track.genre)
                    if len(candidate_genres) >= 3:
                        break

        # Respect Spotify 5-seed limit
        total_seeds = len(seed_artists) + len(candidate_genres)
        if total_seeds > 5:
            # Prioritize genres, limit artists
            max_artists = max(1, 5 - len(candidate_genres))
            seed_artists = seed_artists[:max_artists]
            remaining = 5 - len(seed_artists)
            candidate_genres = candidate_genres[:remaining]

        return {
            "exploration_ratio": exploration_ratio,
            "candidate_genres": candidate_genres,
            "seed_artists": seed_artists,
            "novelty_weight": novelty_weight,
            "taste_similarity_weight": taste_weight,
            "diversity_weight": diversity_weight,
        }

    @staticmethod
    def format_taste_summary(profile) -> str:
        """Format TasteProfile into a summary string for Claude prompts."""
        if profile is None:
            return "No taste profile yet — first-time discovery."

        parts = []

        genre_prefs = profile.genre_preferences or {}
        if genre_prefs:
            top_genres = sorted(genre_prefs.items(), key=lambda x: x[1], reverse=True)[:5]
            genre_str = ", ".join(f"{g} ({w:.2f})" for g, w in top_genres)
            parts.append(f"Preferred genres: {genre_str}")

        parts.append(f"Energy preference: {profile.energy_preference:.2f}")

        fav = profile.favorite_artists or []
        if fav:
            parts.append(f"Favorite artists: {', '.join(fav[:5])}")

        return "\n".join(parts) if parts else "Minimal taste data available."
