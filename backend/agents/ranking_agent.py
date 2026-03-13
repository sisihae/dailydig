from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import repositories as repo


class RankingAgent:
    async def rank_and_select(
        self,
        session: AsyncSession,
        candidates: list[dict],
        strategy: dict,
    ) -> dict:
        """
        Score all candidates, select best for today, queue the rest.

        Scoring formula:
            score = taste_weight * taste_score
                  + novelty_weight * novelty_score
                  + diversity_weight * artist_diversity

        Returns: {
            "selected": candidate dict with score,
            "remaining": list of remaining candidates,
            "score": float,
            "score_breakdown": {taste, novelty, diversity}
        }
        """
        profile = await repo.get_taste_profile(session)
        recent_recs = await repo.get_recent_recommendations(session, days=30)

        # Extract recent recommended artist names for diversity scoring
        recent_artists = []
        for rec in recent_recs[:7]:
            track = await repo.get_track_by_id(session, rec.track_id)
            if track:
                recent_artists.append(track.artist)

        # All-time recommended artists for novelty scoring
        all_recs = await repo.get_recent_recommendations(session, days=365)
        all_recommended_artists = set()
        recent_30d_artists = set()
        for rec in all_recs:
            track = await repo.get_track_by_id(session, rec.track_id)
            if track:
                all_recommended_artists.add(track.artist)
                if rec.recommended_at > datetime.now(timezone.utc) - timedelta(days=30):
                    recent_30d_artists.add(track.artist)

        taste_weight = strategy.get("taste_similarity_weight", 0.5)
        novelty_weight = strategy.get("novelty_weight", 0.3)
        diversity_weight = strategy.get("diversity_weight", 0.2)

        scored = []
        for candidate in candidates:
            taste = self._taste_score(candidate, profile)
            novelty = self._novelty_score(
                candidate, all_recommended_artists, recent_30d_artists
            )
            diversity = self._diversity_score(candidate, recent_artists)

            total = (
                taste_weight * taste
                + novelty_weight * novelty
                + diversity_weight * diversity
            )

            scored.append({
                **candidate,
                "score": total,
                "score_breakdown": {
                    "taste": round(taste, 3),
                    "novelty": round(novelty, 3),
                    "diversity": round(diversity, 3),
                },
            })

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)

        if not scored:
            return {"selected": None, "remaining": [], "score": 0, "score_breakdown": {}}

        selected = scored[0]
        remaining = scored[1:]

        return {
            "selected": selected,
            "remaining": remaining,
            "score": selected["score"],
            "score_breakdown": selected["score_breakdown"],
        }

    @staticmethod
    def _taste_score(candidate: dict, profile) -> float:
        """
        Cosine-like similarity between track features and user preferences.
        Factors: energy distance, genre overlap.
        """
        if profile is None:
            return 0.5  # neutral during cold start

        score = 0.5  # base

        # Energy similarity (closer = higher score)
        if candidate.get("energy") is not None and profile.energy_preference:
            energy_dist = abs(candidate["energy"] - profile.energy_preference)
            score += 0.25 * (1.0 - energy_dist)

        # Genre overlap
        genre = candidate.get("genre")
        if genre and profile.genre_preferences:
            genre_pref = profile.genre_preferences.get(genre, 0.0)
            score += 0.25 * genre_pref

        return min(1.0, max(0.0, score))

    @staticmethod
    def _novelty_score(
        candidate: dict,
        all_recommended_artists: set,
        recent_30d_artists: set,
    ) -> float:
        """
        1.0 if artist never recommended.
        0.5 if recommended but not in last 30 days.
        0.0 if recommended in last 30 days.
        """
        artist = candidate.get("artist", "")
        if artist not in all_recommended_artists:
            return 1.0
        if artist not in recent_30d_artists:
            return 0.5
        return 0.0

    @staticmethod
    def _diversity_score(candidate: dict, recent_artists: list) -> float:
        """
        1.0 if artist not in last 7 recommendations.
        Linearly decreasing if recently recommended.
        """
        artist = candidate.get("artist", "")
        if artist not in recent_artists:
            return 1.0
        # Position in recent list (0 = most recent)
        idx = recent_artists.index(artist)
        return idx / max(len(recent_artists), 1)

    async def queue_remaining(
        self, session: AsyncSession, remaining: list[dict]
    ) -> int:
        """
        Add remaining candidates to dig_queue with source="auto_fetch".
        Returns count of tracks added.
        """
        added = 0
        for candidate in remaining:
            # Create track in DB if not exists
            existing = await repo.get_track_by_spotify_id(session, candidate["spotify_id"])
            if existing:
                track_id = existing.id
            else:
                track = await repo.create_track(
                    session,
                    name=candidate["name"],
                    artist=candidate["artist"],
                    album=candidate.get("album"),
                    spotify_id=candidate["spotify_id"],
                    genre=candidate.get("genre"),
                    energy=candidate.get("energy"),
                    valence=candidate.get("valence"),
                    tempo=candidate.get("tempo"),
                )
                track_id = track.id

            await repo.add_to_queue(session, track_id=track_id, source="auto_fetch")
            added += 1

        return added
