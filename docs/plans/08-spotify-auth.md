# Plan 08 — Spotify OAuth Flow

**Phase**: 2 – Spotify Integration + Playlist Import  
**Creates**: `backend/services/spotify_auth.py`, OAuth route endpoints  
**Depends on**: 03 (config with Spotify credentials)

---

## Goal

Implement Spotify Authorization Code flow for private playlist access. Client Credentials flow for public API calls.

## Steps

### 1. Create `backend/services/__init__.py`

Empty file.

### 2. Create `backend/services/spotify_auth.py`

```python
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

from backend.config import settings

SCOPES = "playlist-read-private playlist-read-collaborative"


def get_spotify_oauth() -> SpotifyOAuth:
    """OAuth manager for Authorization Code flow (private playlists)."""
    return SpotifyOAuth(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
        scope=SCOPES,
    )


def get_spotify_client() -> spotipy.Spotify:
    """
    Returns an authenticated Spotify client.
    Uses refresh token if available, otherwise falls back to Client Credentials.
    """
    if settings.spotify_refresh_token:
        oauth = get_spotify_oauth()
        token_info = oauth.refresh_access_token(settings.spotify_refresh_token)
        return spotipy.Spotify(auth=token_info["access_token"])

    # Fallback: Client Credentials (public playlists only)
    auth_manager = SpotifyClientCredentials(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
    )
    return spotipy.Spotify(auth_manager=auth_manager)
```

### 3. Create OAuth API routes

File: `backend/routes/auth.py`

```python
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from backend.services.spotify_auth import get_spotify_oauth

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/spotify")
async def spotify_auth():
    """Redirect user to Spotify authorization page."""
    oauth = get_spotify_oauth()
    auth_url = oauth.get_authorize_url()
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def spotify_callback(code: str):
    """
    Spotify OAuth callback.
    Exchanges authorization code for tokens.
    Returns refresh_token for the user to save in .env.
    """
    oauth = get_spotify_oauth()
    token_info = oauth.get_access_token(code)
    return {
        "message": "Save this refresh_token in your .env file as SPOTIFY_REFRESH_TOKEN",
        "refresh_token": token_info["refresh_token"],
    }
```

### 4. Register router in `backend/app.py`

```python
from backend.routes.auth import router as auth_router
app.include_router(auth_router)
```

## Key Decisions

- Refresh token stored in `.env` after first-time OAuth flow (single-user, no DB token storage needed).
- `get_spotify_client()` auto-refreshes tokens on each call.
- Falls back to Client Credentials if no refresh token set (public playlists only).

## Verification

1. Start app, visit `http://localhost:8000/auth/spotify`
2. Authorize on Spotify
3. Callback returns `refresh_token`
4. Add to `.env`, restart app
5. `get_spotify_client()` uses refresh token

## Output

- `backend/services/spotify_auth.py` — OAuth manager + client factory
- `backend/routes/auth.py` — `/auth/spotify` and `/auth/callback`
