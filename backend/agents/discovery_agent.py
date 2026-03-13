from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import repositories as repo
from backend.services.spotify_service import SpotifyService

if TYPE_CHECKING:
    from backend.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)


class DiscoveryAgent:
    def __init__(self, spotify_service: SpotifyService):
        self.spotify = spotify_service

    async def fetch_candidates(
        self,
        session: AsyncSession,
        strategy: dict,
        kg_service: KnowledgeGraphService | None = None,
    ) -> list[dict]:
        """
        Fetch candidate tracks from Spotify based on planner strategy.

        Steps:
        1. Optionally expand seed artists using knowledge graph
        2. Call Spotify recommendations with seed artists + genres
        3. Fetch audio features for all candidates
        4. Filter out already recommended or queued tracks (dedup)
        5. Return 30-50 enriched candidate dicts
        """
        seed_artists = list(strategy.get("seed_artists", []))
        seed_genres = strategy.get("candidate_genres", [])

        # Expand seeds from knowledge graph if available
        if kg_service and seed_artists:
            for artist in seed_artists[:3]:
                related = await kg_service.get_related_artists(artist)
                seed_artists.extend(related[:2])
            seed_artists = list(dict.fromkeys(seed_artists))  # dedup, preserve order
            logger.info("Expanded seed artists via knowledge graph: %s", seed_artists)

        # Fetch recommendations from Spotify (cached for 1h)
        raw_tracks = await self.spotify.get_recommendations(
            seed_artists=seed_artists if seed_artists else None,
            seed_genres=seed_genres if seed_genres else None,
            limit=50,
        )

        if not raw_tracks:
            return []

        # Fetch audio features
        track_ids = [t["spotify_id"] for t in raw_tracks]
        audio_features = await self.spotify.get_track_audio_features(track_ids)

        # Dedup: filter out already recommended or queued tracks
        candidates = []
        for raw in raw_tracks:
            # Check if already in DB
            existing = await repo.get_track_by_spotify_id(session, raw["spotify_id"])

            if existing:
                already_recommended = await repo.is_track_recommended(session, existing.id)
                in_queue = await repo.is_track_in_queue(session, existing.id)
                if already_recommended or in_queue:
                    continue

            # Fetch genre from artist if not already known
            genre = None
            if raw.get("artist_id"):
                genres = await self.spotify.get_artist_genres(raw["artist_id"])
                genre = genres[0] if genres else None

            features = audio_features.get(raw["spotify_id"], {})

            candidates.append({
                "spotify_id": raw["spotify_id"],
                "name": raw["name"],
                "artist": raw["artist"],
                "artist_id": raw.get("artist_id"),
                "album": raw.get("album"),
                "genre": genre,
                "energy": features.get("energy"),
                "valence": features.get("valence"),
                "tempo": features.get("tempo"),
            })

        return candidates
