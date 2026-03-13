import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

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
