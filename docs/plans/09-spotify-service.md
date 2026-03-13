# Plan 09 — Spotify Service

**Phase**: 2 – Spotify Integration + Playlist Import  
**Creates**: `backend/services/spotify_service.py`  
**Depends on**: 08 (spotify_auth with `get_spotify_client`)

---

## Goal

Wrap all Spotify Web API interactions into a service class with Redis caching.

## Steps

### 1. Create `backend/services/spotify_service.py`

```python
import re
import json

import redis.asyncio as aioredis
import spotipy

from backend.config import settings
from backend.services.spotify_auth import get_spotify_client


class SpotifyService:
    def __init__(self):
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url)
        return self._redis

    def _get_client(self) -> spotipy.Spotify:
        return get_spotify_client()

    @staticmethod
    def parse_playlist_id(url_or_id: str) -> str:
        """Extract playlist ID from a Spotify URL or URI."""
        patterns = [
            r"playlist/([a-zA-Z0-9]+)",      # URL format
            r"playlist:([a-zA-Z0-9]+)",        # URI format
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        return url_or_id  # assume raw ID

    async def get_playlist_tracks(self, playlist_id: str) -> list[dict]:
        """
        Fetch all tracks from a playlist (handles pagination).
        Returns list of simplified track dicts.
        """
        sp = self._get_client()
        tracks = []
        results = sp.playlist_tracks(playlist_id)

        while results:
            for item in results["items"]:
                track = item.get("track")
                if track and track.get("id"):
                    tracks.append({
                        "spotify_id": track["id"],
                        "name": track["name"],
                        "artist": ", ".join(a["name"] for a in track["artists"]),
                        "artist_id": track["artists"][0]["id"] if track["artists"] else None,
                        "album": track.get("album", {}).get("name"),
                    })
            results = sp.next(results) if results.get("next") else None

        return tracks

    async def get_track_audio_features(self, track_ids: list[str]) -> dict[str, dict]:
        """
        Fetch audio features for multiple tracks.
        Returns {spotify_id: {energy, valence, tempo}} with Redis caching (TTL 24h).
        """
        redis = await self._get_redis()
        result = {}
        uncached_ids = []

        # Check cache first
        for tid in track_ids:
            cached = await redis.get(f"audio_features:{tid}")
            if cached:
                result[tid] = json.loads(cached)
            else:
                uncached_ids.append(tid)

        # Fetch uncached in batches of 100 (Spotify API limit)
        if uncached_ids:
            sp = self._get_client()
            for i in range(0, len(uncached_ids), 100):
                batch = uncached_ids[i : i + 100]
                features = sp.audio_features(batch)
                for feat in features:
                    if feat:
                        data = {
                            "energy": feat.get("energy"),
                            "valence": feat.get("valence"),
                            "tempo": feat.get("tempo"),
                        }
                        result[feat["id"]] = data
                        await redis.set(
                            f"audio_features:{feat['id']}",
                            json.dumps(data),
                            ex=86400,  # 24 hours
                        )

        return result

    async def get_recommendations(
        self,
        seed_artists: list[str] | None = None,
        seed_genres: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        Fetch recommendations from Spotify.
        Max 5 seeds total (artists + genres).
        Redis cached for 1 hour.
        """
        redis = await self._get_redis()
        cache_key = f"recs:{':'.join(seed_artists or [])}:{':'.join(seed_genres or [])}:{limit}"
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        sp = self._get_client()
        results = sp.recommendations(
            seed_artists=seed_artists or [],
            seed_genres=seed_genres or [],
            limit=limit,
        )

        tracks = []
        for track in results.get("tracks", []):
            tracks.append({
                "spotify_id": track["id"],
                "name": track["name"],
                "artist": ", ".join(a["name"] for a in track["artists"]),
                "artist_id": track["artists"][0]["id"] if track["artists"] else None,
                "album": track.get("album", {}).get("name"),
            })

        await redis.set(cache_key, json.dumps(tracks), ex=3600)  # 1 hour

        return tracks

    async def get_artist_genres(self, artist_id: str) -> list[str]:
        """Fetch genres for an artist."""
        sp = self._get_client()
        artist = sp.artist(artist_id)
        return artist.get("genres", [])
```

## Key Decisions

- Redis caching: audio features (24h), recommendations (1h).
- Pagination handling for large playlists.
- Batch audio features in groups of 100 (Spotify limit).
- `parse_playlist_id` handles URL, URI, and raw ID formats.

## Verification

```python
service = SpotifyService()
tracks = await service.get_playlist_tracks("37i9dQZF1DXcBWIGoYBM5M")
print(len(tracks), tracks[0]["name"])
```

## Output

- `backend/services/spotify_service.py` — Full Spotify API wrapper with caching
