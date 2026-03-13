import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_session
from backend.services.queue_service import QueueService
from backend.services.spotify_service import SpotifyService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["playlist"])


class ImportPlaylistRequest(BaseModel):
    playlist_url: str


class ImportPlaylistResponse(BaseModel):
    imported: int
    duplicates_skipped: int
    queue_total: int


@router.post("/import-playlist", response_model=ImportPlaylistResponse)
async def import_playlist(
    body: ImportPlaylistRequest,
    session: AsyncSession = Depends(get_session),
):
    """Import a Spotify playlist into the dig queue."""
    try:
        spotify_service = SpotifyService()
        queue_service = QueueService(spotify_service)
        result = await queue_service.import_playlist(session, body.playlist_url)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Spotify API error during playlist import")
        raise HTTPException(status_code=502, detail=f"Spotify API error: {exc}")


@router.get("/queue")
async def get_queue(session: AsyncSession = Depends(get_session)):
    """View all pending tracks in the dig queue."""
    spotify_service = SpotifyService()
    queue_service = QueueService(spotify_service)
    return await queue_service.get_queue_status(session)
