# 7. Spotify Integration

## Authentication

Spotify's Recommendations API requires **Client Credentials** flow (no user data needed).
Playlist fetching for public playlists also works with Client Credentials.

For private playlists, the **Authorization Code flow** is needed:

- `GET /auth/spotify` → redirect user to Spotify authorization page
- `GET /auth/callback` → receive authorization code, exchange for refresh token

After first-time auth, store `SPOTIFY_REFRESH_TOKEN` in `.env`. The service auto-refreshes access tokens using the refresh token.

---

## Service Methods

```python
class SpotifyService:
    get_playlist_tracks(playlist_id: str) -> list[Track]    # for playlist import
    get_track(track_id: str) -> Track                        # single track lookup
    get_recommendations(seed_artists, seed_genres, limit=50) -> list[Track]  # auto-discovery
    get_track_audio_features(track_ids: list[str]) -> list[AudioFeatures]
    get_artist(artist_id: str) -> Artist                     # for genre info
```

Note: `get_user_top_tracks` and `get_user_top_artists` are NOT used (no taste bootstrapping).

---

## Playlist Import

`POST /import-playlist` endpoint:

1. Parse Spotify playlist URL to extract playlist ID
2. Call `get_playlist_tracks(playlist_id)` to fetch all tracks
3. Fetch audio features for all tracks
4. Filter out tracks already delivered (dedup against `recommendation_history`)
5. Insert into `dig_queue` table with `source=playlist_import`, `status=pending`
6. Return count of imported tracks

Multiple playlists can be imported — new tracks append to the existing queue.
