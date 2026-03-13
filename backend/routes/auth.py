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
