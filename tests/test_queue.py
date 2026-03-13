from sqlalchemy import select

from backend.database import repositories as repo
from backend.models import DigQueue


class TestQueueOperations:
    async def test_import_adds_tracks_to_queue(self, db_session, sample_track):
        """Track added to queue has status=pending."""
        entry = await repo.add_to_queue(db_session, track_id=sample_track.id, source="playlist_import")
        assert entry.status == "pending"
        assert entry.source == "playlist_import"

    async def test_dedup_skips_existing_tracks(self, db_session, sample_track, sample_queue_entry):
        """Track already in queue should be detected."""
        is_in_queue = await repo.is_track_in_queue(db_session, sample_track.id)
        assert is_in_queue is True

    async def test_pick_random_from_pending(self, db_session, sample_track, sample_queue_entry):
        """Random pick returns a pending entry."""
        entry = await repo.pick_random_pending(db_session)
        assert entry is not None
        assert entry.status == "pending"

    async def test_pick_from_empty_queue_returns_none(self, db_session):
        """Empty queue returns None."""
        entry = await repo.pick_random_pending(db_session)
        assert entry is None

    async def test_mark_delivered(self, db_session, sample_queue_entry):
        """Marking delivered changes status."""
        await repo.mark_delivered(db_session, sample_queue_entry.id)
        await db_session.flush()
        result = await db_session.execute(
            select(DigQueue).where(DigQueue.id == sample_queue_entry.id)
        )
        entry = result.scalar_one()
        assert entry.status == "delivered"
