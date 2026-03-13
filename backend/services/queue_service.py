from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import repositories as repo
from backend.services.spotify_service import SpotifyService


class QueueService:
    def __init__(self, spotify_service: SpotifyService) -> None:
        self.spotify = spotify_service

    async def import_playlist(
        self, session: AsyncSession, playlist_url: str
    ) -> dict:
        """
        Import a Spotify playlist into the dig queue.
        Returns {imported, duplicates_skipped, queue_total}.
        """
        playlist_id = SpotifyService.parse_playlist_id(playlist_url)
        raw_tracks = await self.spotify.get_playlist_tracks(playlist_id)

        # Fetch audio features for all tracks
        track_ids = [t["spotify_id"] for t in raw_tracks]
        audio_features = await self.spotify.get_track_audio_features(track_ids)

        imported = 0
        duplicates_skipped = 0

        for raw in raw_tracks:
            # Check if track already exists in DB
            existing = await repo.get_track_by_spotify_id(session, raw["spotify_id"])

            if existing:
                # Check if already in queue or already recommended (dedup)
                in_queue = await repo.is_track_in_queue(session, existing.id)
                already_recommended = await repo.is_track_recommended(session, existing.id)
                if in_queue or already_recommended:
                    duplicates_skipped += 1
                    continue
                track = existing
            else:
                # Fetch genre from artist
                genre = None
                if raw.get("artist_id"):
                    genres = await self.spotify.get_artist_genres(raw["artist_id"])
                    genre = genres[0] if genres else None

                # Create track with audio features
                features = audio_features.get(raw["spotify_id"], {})
                track = await repo.create_track(
                    session,
                    name=raw["name"],
                    artist=raw["artist"],
                    album=raw["album"],
                    spotify_id=raw["spotify_id"],
                    genre=genre,
                    energy=features.get("energy"),
                    valence=features.get("valence"),
                    tempo=features.get("tempo"),
                )

            # Add to queue
            await repo.add_to_queue(
                session,
                track_id=track.id,
                source="playlist_import",
                playlist_url=playlist_url,
            )
            imported += 1

        await session.commit()

        queue_total = await repo.get_pending_count(session)

        return {
            "imported": imported,
            "duplicates_skipped": duplicates_skipped,
            "queue_total": queue_total,
        }

    async def pick_random_track(self, session: AsyncSession) -> tuple:
        """
        Pick a random pending track from the queue.
        Returns (DigQueue entry, Track) or (None, None) if queue empty.
        """
        queue_entry = await repo.pick_random_pending(session)
        if queue_entry is None:
            return None, None
        track = await repo.get_track_by_id(session, queue_entry.track_id)
        return queue_entry, track

    async def is_queue_empty(self, session: AsyncSession) -> bool:
        count = await repo.get_pending_count(session)
        return count == 0

    async def get_queue_status(self, session: AsyncSession) -> dict:
        """Return pending queue entries with their track details."""
        pending = await repo.get_pending_queue(session)
        total = len(pending)
        tracks = []
        for entry in pending:
            track = await repo.get_track_by_id(session, entry.track_id)
            if track:
                tracks.append(
                    {
                        "queue_id": entry.id,
                        "track_name": track.name,
                        "artist": track.artist,
                        "source": entry.source,
                        "added_at": entry.added_at.isoformat(),
                    }
                )
        return {"pending_count": total, "tracks": tracks}
