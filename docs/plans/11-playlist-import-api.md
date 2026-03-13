# Plan 11 — Playlist Import & Queue API Endpoints

**Phase**: 2 – Spotify Integration + Playlist Import  
**Creates**: `backend/routes/playlist.py`  
**Depends on**: 10 (queue service), 07 (FastAPI app)

---

## Goal

Expose `POST /import-playlist` and `GET /queue` API endpoints.

## Steps

### 1. Create `backend/routes/__init__.py`

Empty file.

### 2. Create `backend/routes/playlist.py`

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_session
from backend.services.spotify_service import SpotifyService
from backend.services.queue_service import QueueService

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
    spotify_service = SpotifyService()
    queue_service = QueueService(spotify_service)
    result = await queue_service.import_playlist(session, body.playlist_url)
    return result


@router.get("/queue")
async def get_queue(session: AsyncSession = Depends(get_session)):
    """View all pending tracks in the dig queue."""
    spotify_service = SpotifyService()
    queue_service = QueueService(spotify_service)
    return await queue_service.get_queue_status(session)
```

### 3. Register router in `backend/app.py`

```python
from backend.routes.playlist import router as playlist_router
app.include_router(playlist_router)
```

## Request/Response Examples

**Import playlist:**

```
POST /import-playlist
{"playlist_url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"}

→ {"imported": 42, "duplicates_skipped": 3, "queue_total": 58}
```

**View queue:**

```
GET /queue

→ {"pending_count": 58, "tracks": [{"queue_id": 1, "track_name": "...", ...}]}
```

## Verification

```bash
curl -X POST http://localhost:8000/import-playlist \
  -H "Content-Type: application/json" \
  -d '{"playlist_url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"}'

curl http://localhost:8000/queue
```

## Output

- `backend/routes/playlist.py` — two endpoints
- Updated `backend/app.py` — router registered
